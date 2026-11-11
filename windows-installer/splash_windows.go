//go:build windows && !hubcli

package main

import (
	"bytes"
	_ "embed"
	"image"
	"image/draw"
	"image/png"
	"math"
	"runtime"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

//go:embed winres/icon-256.png
var splashIconPNG []byte

const (
	splashClassName    = "BrasfootMegaPatchSplash"
	splashIconSize     = 84.0
	splashRadius       = 21.0
	splashStroke       = 3.0
	splashPeriod       = 1600 * time.Millisecond
	splashBreatheLow   = 0.94
	splashBreatheHigh  = 1.04
	splashRingFrom     = 0.96
	splashRingTo       = 1.8
	splashRingOpacity  = 0.42
	splashTimeout      = 45 * time.Second
	splashWmPaint      = 0x000F
	splashWmEraseBkgnd = 0x0014
	splashWmQuit       = 0x0012
	splashPmRemove     = 1
	splashExTopmost    = 0x00000008
	splashExToolWindow = 0x00000080
	splashExNoActivate = 0x08000000
	splashShowNoAct    = 4
	splashNoSize       = 0x0001
	splashNoMove       = 0x0002
	splashNoActivate   = 0x0010
	splashSpiAnimation = 0x1042
	splashCursorArrow  = 32512
	splashSrcCopy      = 0x00CC0020
)

var (
	splashPeekMessage  = u32.NewProc("PeekMessageW")
	splashLoadCursor   = u32.NewProc("LoadCursorW")
	splashForeground   = u32.NewProc("GetForegroundWindow")
	splashWindowThread = u32.NewProc("GetWindowThreadProcessId")
	splashSystemParam  = u32.NewProc("SystemParametersInfoW")
	splashGetDC        = u32.NewProc("GetDC")
	splashReleaseDC    = u32.NewProc("ReleaseDC")
	splashCompatibleDC = g32.NewProc("CreateCompatibleDC")
	splashDIBSection   = g32.NewProc("CreateDIBSection")
	splashSelect       = g32.NewProc("SelectObject")
	splashBitBlt       = g32.NewProc("BitBlt")
	splashDeleteDC     = g32.NewProc("DeleteDC")
	splashExcludeClip  = g32.NewProc("ExcludeClipRect")
	splashDwmFlush     = dwm.NewProc("DwmFlush")
	splashProcessID    = k32.NewProc("GetCurrentProcessId")
	splashSleep        = k32.NewProc("Sleep")

	splashMutex   sync.Mutex
	splashHandle  uintptr
	splashStart   time.Time
	splashClosed  bool
	splashProc    uintptr
	splashPainter *splashCanvas
)

type splashCanvas struct {
	dc, bitmap    uintptr
	pixels        []byte
	work          []float32
	horizontal    []float32
	source        []float32
	sourceSize    int
	side          int
	width, height int
	scale         float64
	fade          bool
	topmost       bool
	brush         uintptr
	background    [3]float32
	accent        [3]float32
	columns, rows []splashSpan
	weights       []float32
}

type splashSpan struct {
	first, count, offset int
}

type splashBitmapInfo struct {
	Size                       uint32
	Width, Height              int32
	Planes, BitCount           uint16
	Compression, ImageSize     uint32
	XPerMeter, YPerMeter       int32
	ColorsUsed, ColorImportant uint32
}

func hubWindowRect() (int, int, int, int) {
	dpi := uintptr(96)
	if getDpiForSystem.Find() == nil {
		dpi, _, _ = getDpiForSystem.Call()
	}
	w, h := hubWidth*int(dpi)/96, hubHeight*int(dpi)/96
	sw, _, _ := getSystemMetrics.Call(0)
	sh, _, _ := getSystemMetrics.Call(1)
	if w > int(sw)-24 {
		w = int(sw) - 24
	}
	if h > int(sh)-48 {
		h = int(sh) - 48
	}
	return (int(sw) - w) / 2, (int(sh) - h) / 2, w, h
}

func showSplash(dark bool) {
	splashStart = time.Now()
	ready := make(chan struct{}, 1)
	go func() {
		runtime.LockOSThread()
		defer runtime.UnlockOSThread()
		splashRun(dark, ready)
	}()
	select {
	case <-ready:
	case <-time.After(2 * time.Second):
	}
	time.AfterFunc(splashTimeout, closeSplash)
}

func closeSplash() {
	splashMutex.Lock()
	defer splashMutex.Unlock()
	splashClosed = true
	if splashHandle != 0 {
		postMessage.Call(splashHandle, wmClose, 0, 0)
	}
}

func splashPhase() float64 {
	if splashStart.IsZero() {
		return 0
	}
	return float64(time.Since(splashStart).Microseconds()) / 1000
}

func splashAlive() bool {
	splashMutex.Lock()
	defer splashMutex.Unlock()
	return splashHandle != 0
}

func splashRun(dark bool, ready chan struct{}) {
	signal := func() {
		select {
		case ready <- struct{}{}:
		default:
		}
	}
	defer signal()
	x, y, w, h := hubWindowRect()
	dpi := uintptr(96)
	if getDpiForSystem.Find() == nil {
		dpi, _, _ = getDpiForSystem.Call()
	}
	var animate int32 = 1
	splashSystemParam.Call(splashSpiAnimation, 0, uintptr(unsafe.Pointer(&animate)), 0)
	canvas := &splashCanvas{width: w, height: h, scale: float64(dpi) / 96, fade: animate == 0, topmost: true}
	background := [3]byte{0xff, 0xff, 0xff}
	canvas.accent = [3]float32{0x0b, 0x4b, 0xe0}
	border := uint32(0x00f3e7e1)
	if dark {
		background, border = [3]byte{0x0b, 0x12, 0x20}, 0x0020120b
		canvas.accent = [3]float32{0x5b, 0x8c, 0xff}
	}
	canvas.background = [3]float32{float32(background[0]), float32(background[1]), float32(background[2])}
	canvas.brush, _, _ = newBrush.Call(color(background[0], background[1], background[2]))
	if !canvas.prepare() {
		return
	}
	defer canvas.release()
	splashPainter = canvas
	instance, _, _ := getModule.Call(0)
	cursor, _, _ := splashLoadCursor.Call(0, splashCursorArrow)
	splashProc = syscall.NewCallback(splashWindowProcedure)
	class := winClass{
		Procedure: splashProc, Instance: instance, Cursor: cursor, Background: canvas.brush,
		ClassName: strPtr(splashClassName),
	}
	class.Size = uint32(unsafe.Sizeof(class))
	registerClass.Call(uintptr(unsafe.Pointer(&class)))
	handle, _, _ := createWindow.Call(splashExTopmost|splashExToolWindow|splashExNoActivate,
		uintptr(unsafe.Pointer(strPtr(splashClassName))), uintptr(unsafe.Pointer(strPtr(productName))),
		wsPopup, uintptr(x), uintptr(y), uintptr(w), uintptr(h), 0, 0, instance, 0)
	if handle == 0 {
		return
	}
	if dwm.Load() == nil {
		corner := uint32(dwmCornerRound)
		dwmSetAttribute.Call(handle, dwmCornerAttr, uintptr(unsafe.Pointer(&corner)), 4)
		dwmSetAttribute.Call(handle, dwmBorderColor, uintptr(unsafe.Pointer(&border)), 4)
	}
	splashMutex.Lock()
	if splashClosed {
		splashMutex.Unlock()
		pixDestroyWindow.Call(handle)
		return
	}
	splashHandle = handle
	splashMutex.Unlock()
	canvas.render(time.Since(splashStart))
	showWindow.Call(handle, splashShowNoAct)
	updateWindow.Call(handle)
	signal()
	flush := dwm.Load() == nil && splashDwmFlush.Find() == nil
	var message winMessage
	for {
		for {
			result, _, _ := splashPeekMessage.Call(uintptr(unsafe.Pointer(&message)), 0, 0, 0, splashPmRemove)
			if result == 0 {
				break
			}
			if message.Msg == splashWmQuit {
				return
			}
			translateMessage.Call(uintptr(unsafe.Pointer(&message)))
			dispatchMessage.Call(uintptr(unsafe.Pointer(&message)))
		}
		if !splashAlive() {
			splashSleep.Call(8)
			continue
		}
		canvas.keepOrder(handle)
		canvas.render(time.Since(splashStart))
		canvas.present(handle)
		if !flush {
			splashSleep.Call(8)
		} else if result, _, _ := splashDwmFlush.Call(); result != 0 {
			splashSleep.Call(8)
		}
	}
}

func splashWindowProcedure(window uintptr, message uint32, w, l uintptr) uintptr {
	switch message {
	case splashWmEraseBkgnd:
		return 1
	case splashWmPaint:
		ps := pixPaintStruct{}
		hdc, _, _ := pixBeginPaint.Call(window, uintptr(unsafe.Pointer(&ps)))
		if hdc != 0 {
			if splashPainter != nil {
				splashPainter.blit(hdc)
				box := splashPainter.box()
				splashExcludeClip.Call(hdc, uintptr(box.Left), uintptr(box.Top), uintptr(box.Right), uintptr(box.Bottom))
				pixFillRect.Call(hdc, uintptr(unsafe.Pointer(&ps.Rectangle)), splashPainter.brush)
			}
			pixEndPaint.Call(window, uintptr(unsafe.Pointer(&ps)))
		}
		return 0
	case wmClose:
		pixDestroyWindow.Call(window)
		return 0
	case wmDestroy:
		splashMutex.Lock()
		splashHandle = 0
		splashMutex.Unlock()
		quitMessage.Call(0)
		return 0
	}
	result, _, _ := defWindow.Call(window, uintptr(message), w, l)
	return result
}

func (c *splashCanvas) keepOrder(window uintptr) {
	foreground, _, _ := splashForeground.Call()
	var owner uint32
	if foreground != 0 {
		splashWindowThread.Call(foreground, uintptr(unsafe.Pointer(&owner)))
	}
	self, _, _ := splashProcessID.Call()
	ours := foreground == 0 || uintptr(owner) == self
	if ours == c.topmost {
		return
	}
	after := foreground
	if ours {
		after = ^uintptr(0)
	}
	setWindowPos.Call(window, after, 0, 0, 0, 0, splashNoMove|splashNoSize|splashNoActivate)
	c.topmost = ours
}

func (c *splashCanvas) box() rect {
	left := int32((c.width - c.side) / 2)
	top := int32((c.height - c.side) / 2)
	return rect{left, top, left + int32(c.side), top + int32(c.side)}
}

func (c *splashCanvas) blit(hdc uintptr) {
	box := c.box()
	splashBitBlt.Call(hdc, uintptr(box.Left), uintptr(box.Top), uintptr(c.side), uintptr(c.side), c.dc, 0, 0, splashSrcCopy)
}

func (c *splashCanvas) present(window uintptr) {
	hdc, _, _ := splashGetDC.Call(window)
	if hdc == 0 {
		return
	}
	c.blit(hdc)
	splashReleaseDC.Call(window, hdc)
}

func (c *splashCanvas) prepare() bool {
	decoded, err := png.Decode(bytes.NewReader(splashIconPNG))
	if err != nil {
		return false
	}
	source := image.NewNRGBA(decoded.Bounds())
	draw.Draw(source, source.Bounds(), decoded, decoded.Bounds().Min, draw.Src)
	if source.Bounds().Dx() != source.Bounds().Dy() {
		return false
	}
	c.sourceSize = source.Bounds().Dx()
	c.source = make([]float32, len(source.Pix))
	for i := 0; i < len(source.Pix); i += 4 {
		a := float32(source.Pix[i+3]) / 255
		c.source[i] = float32(source.Pix[i]) * a
		c.source[i+1] = float32(source.Pix[i+1]) * a
		c.source[i+2] = float32(source.Pix[i+2]) * a
		c.source[i+3] = a
	}
	reach := splashBreatheHigh
	if !c.fade {
		reach = splashRingTo
	}
	c.side = int(math.Ceil(splashIconSize*c.scale*reach)) + 4
	c.side = min(c.side, c.width, c.height)
	info := splashBitmapInfo{Width: int32(c.side), Height: -int32(c.side), Planes: 1, BitCount: 32}
	info.Size = uint32(unsafe.Sizeof(info))
	var bits unsafe.Pointer
	c.bitmap, _, _ = splashDIBSection.Call(0, uintptr(unsafe.Pointer(&info)), 0, uintptr(unsafe.Pointer(&bits)), 0, 0)
	if c.bitmap == 0 || bits == nil {
		return false
	}
	c.pixels = unsafe.Slice((*byte)(bits), c.side*c.side*4)
	c.dc, _, _ = splashCompatibleDC.Call(0)
	splashSelect.Call(c.dc, c.bitmap)
	c.work = make([]float32, c.side*c.side*3)
	c.horizontal = make([]float32, c.side*c.sourceSize*4)
	return true
}

func (c *splashCanvas) release() {
	if c.dc != 0 {
		splashDeleteDC.Call(c.dc)
	}
	if c.bitmap != 0 {
		pixDeleteObject.Call(c.bitmap)
	}
	c.dc, c.bitmap, c.pixels = 0, 0, nil
}

func splashBezier(x1, y1, x2, y2, p float64) float64 {
	low, high := 0.0, 1.0
	for i := 0; i < 22; i++ {
		t := (low + high) / 2
		x := 3*(1-t)*(1-t)*t*x1 + 3*(1-t)*t*t*x2 + t*t*t
		if x < p {
			low = t
		} else {
			high = t
		}
	}
	t := (low + high) / 2
	return 3*(1-t)*(1-t)*t*y1 + 3*(1-t)*t*t*y2 + t*t*t
}

func splashRoundedDistance(x, y, half, radius float64) float64 {
	qx := math.Abs(x) - (half - radius)
	qy := math.Abs(y) - (half - radius)
	outside := math.Hypot(math.Max(qx, 0), math.Max(qy, 0))
	inside := math.Min(math.Max(qx, qy), 0)
	return outside + inside - radius
}

func splashByte(value float32) byte {
	return byte(math.Max(0, math.Min(255, float64(value)+0.5)))
}

func (c *splashCanvas) render(elapsed time.Duration) {
	cycle := float64(elapsed%splashPeriod) / float64(splashPeriod)
	swing := cycle * 2
	if swing > 1 {
		swing = 2 - swing
	}
	ease := splashBezier(0.42, 0, 0.58, 1, swing)
	for i := 0; i < c.side*c.side; i++ {
		c.work[i*3], c.work[i*3+1], c.work[i*3+2] = c.background[0], c.background[1], c.background[2]
	}
	scale, opacity := splashBreatheLow+(splashBreatheHigh-splashBreatheLow)*ease, 1.0
	if c.fade {
		scale, opacity = 1, 0.6+0.4*ease
	} else {
		c.ring(math.Mod(cycle+0.5, 1))
		c.ring(cycle)
	}
	c.icon(scale, opacity)
	for i := 0; i < c.side*c.side; i++ {
		c.pixels[i*4] = splashByte(c.work[i*3+2])
		c.pixels[i*4+1] = splashByte(c.work[i*3+1])
		c.pixels[i*4+2] = splashByte(c.work[i*3])
		c.pixels[i*4+3] = 255
	}
}

func (c *splashCanvas) ring(progress float64) {
	ease := splashBezier(0.2, 0.6, 0.35, 1, progress)
	grow := splashRingFrom + (splashRingTo-splashRingFrom)*ease
	alpha := splashRingOpacity * (1 - ease)
	if alpha < 0.003 {
		return
	}
	half := splashIconSize * c.scale / 2
	radius := splashRadius * c.scale
	stroke := splashStroke * c.scale * grow
	center := float64(c.side) / 2
	extent := half*grow + 2
	first := int(math.Max(0, math.Floor(center-extent)))
	last := int(math.Min(float64(c.side), math.Ceil(center+extent)))
	inner := half*grow - stroke - 2
	for y := first; y < last; y++ {
		py := float64(y) + 0.5 - center
		for x := first; x < last; x++ {
			px := float64(x) + 0.5 - center
			if math.Abs(px) < inner-radius*grow && math.Abs(py) < inner {
				continue
			}
			d := splashRoundedDistance(px/grow, py/grow, half, radius) * grow
			coverage := math.Max(0, math.Min(1, 0.5-d)) * math.Max(0, math.Min(1, 0.5+d+stroke))
			if coverage <= 0 {
				continue
			}
			a := float32(coverage * alpha)
			index := (y*c.side + x) * 3
			for k := 0; k < 3; k++ {
				c.work[index+k] += (c.accent[k] - c.work[index+k]) * a
			}
		}
	}
}

func (c *splashCanvas) spans(size, origin float64, spans []splashSpan) ([]splashSpan, int) {
	step := float64(c.sourceSize) / size
	first := int(math.Max(0, math.Floor(origin)))
	last := int(math.Min(float64(c.side), math.Ceil(origin+size)))
	spans = spans[:0]
	for d := first; d < last; d++ {
		low := math.Max(0, (float64(d)-origin)*step)
		high := math.Min(float64(c.sourceSize), (float64(d+1)-origin)*step)
		span := splashSpan{offset: len(c.weights)}
		if high > low {
			span.first = int(math.Floor(low))
			for j := span.first; float64(j) < high && j < c.sourceSize; j++ {
				weight := math.Min(high, float64(j+1)) - math.Max(low, float64(j))
				c.weights = append(c.weights, float32(weight/step))
				span.count++
			}
		}
		spans = append(spans, span)
	}
	return spans, first
}

func (c *splashCanvas) icon(scale, opacity float64) {
	size := splashIconSize * c.scale * scale
	origin := float64(c.side)/2 - size/2
	c.weights = c.weights[:0]
	var x0, y0 int
	c.columns, x0 = c.spans(size, origin, c.columns)
	c.rows, y0 = c.spans(size, origin, c.rows)
	n := c.sourceSize
	width := len(c.columns)
	for sy := 0; sy < n; sy++ {
		row := c.source[sy*n*4 : (sy+1)*n*4]
		out := c.horizontal[sy*width*4:]
		for i, span := range c.columns {
			var r, g, b, a float32
			for k := 0; k < span.count; k++ {
				w := c.weights[span.offset+k]
				p := (span.first + k) * 4
				r += row[p] * w
				g += row[p+1] * w
				b += row[p+2] * w
				a += row[p+3] * w
			}
			out[i*4], out[i*4+1], out[i*4+2], out[i*4+3] = r, g, b, a
		}
	}
	o := float32(opacity)
	for j, span := range c.rows {
		y := y0 + j
		for i := 0; i < width; i++ {
			var r, g, b, a float32
			for k := 0; k < span.count; k++ {
				w := c.weights[span.offset+k]
				p := ((span.first+k)*width + i) * 4
				r += c.horizontal[p] * w
				g += c.horizontal[p+1] * w
				b += c.horizontal[p+2] * w
				a += c.horizontal[p+3] * w
			}
			if a <= 0 {
				continue
			}
			a = min(a, 1)
			index := (y*c.side + x0 + i) * 3
			keep := 1 - a*o
			c.work[index] = c.work[index]*keep + r*o
			c.work[index+1] = c.work[index+1]*keep + g*o
			c.work[index+2] = c.work[index+2]*keep + b*o
		}
	}
}
