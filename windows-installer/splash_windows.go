//go:build windows

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
	splashIconSize     = 84
	splashMinScale     = 0.9
	splashMaxScale     = 1.06
	splashPulsePeriod  = 1400 * time.Millisecond
	splashFadePeriod   = 1600 * time.Millisecond
	splashTimerID      = 1
	splashTimeout      = 45 * time.Second
	splashWmPaint      = 0x000F
	splashWmEraseBkgnd = 0x0014
	splashWmTimer      = 0x0113
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
	splashMsimg        = syscall.NewLazyDLL("msimg32.dll")
	splashAlphaBlend   = splashMsimg.NewProc("AlphaBlend")
	splashSetTimer     = u32.NewProc("SetTimer")
	splashKillTimer    = u32.NewProc("KillTimer")
	splashInvalidate   = u32.NewProc("InvalidateRect")
	splashLoadCursor   = u32.NewProc("LoadCursorW")
	splashForeground   = u32.NewProc("GetForegroundWindow")
	splashWindowThread = u32.NewProc("GetWindowThreadProcessId")
	splashSystemParam  = u32.NewProc("SystemParametersInfoW")
	splashCompatibleDC = g32.NewProc("CreateCompatibleDC")
	splashCompatBitmap = g32.NewProc("CreateCompatibleBitmap")
	splashDIBSection   = g32.NewProc("CreateDIBSection")
	splashSelect       = g32.NewProc("SelectObject")
	splashGetDC        = u32.NewProc("GetDC")
	splashReleaseDC    = u32.NewProc("ReleaseDC")
	splashBitBlt       = g32.NewProc("BitBlt")
	splashDeleteDC     = g32.NewProc("DeleteDC")
	splashExcludeClip  = g32.NewProc("ExcludeClipRect")
	splashProcessID    = k32.NewProc("GetCurrentProcessId")

	splashMutex    sync.Mutex
	splashHandle   uintptr
	splashStart    time.Time
	splashClosed   bool
	splashBrush    uintptr
	splashBuffer   uintptr
	splashBufferBM uintptr
	splashSide     int
	splashFade     bool
	splashTopmost  bool
	splashFrames   map[int]splashFrame
	splashWidth    int
	splashHeight   int
	splashProc     uintptr
	splashBase     int
)

type splashFrame struct {
	dc, bitmap uintptr
	size       int
}

type splashBitmapInfo struct {
	Size                       uint32
	Width, Height              int32
	Planes, BitCount           uint16
	Compression, ImageSize     uint32
	XPerMeter, YPerMeter       int32
	ColorsUsed, ColorImportant uint32
}

type splashBlend struct {
	Op, Flags, Alpha, Format byte
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
	return float64(time.Since(splashStart).Milliseconds())
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
	splashWidth, splashHeight = w, h
	dpi := uintptr(96)
	if getDpiForSystem.Find() == nil {
		dpi, _, _ = getDpiForSystem.Call()
	}
	var animate int32 = 1
	splashSystemParam.Call(splashSpiAnimation, 0, uintptr(unsafe.Pointer(&animate)), 0)
	splashFade = animate == 0
	background := color(255, 255, 255)
	border := uint32(0x00f3e7e1)
	if dark {
		background, border = color(0x0b, 0x12, 0x20), 0x0020120b
	}
	splashBrush, _, _ = newBrush.Call(background)
	base := float64(splashIconSize) * float64(dpi) / 96
	if !splashPrepare(base) {
		return
	}
	instance, _, _ := getModule.Call(0)
	cursor, _, _ := splashLoadCursor.Call(0, splashCursorArrow)
	splashProc = syscall.NewCallback(splashWindowProcedure)
	class := winClass{
		Procedure: splashProc, Instance: instance, Cursor: cursor, Background: splashBrush,
		ClassName: strPtr(splashClassName),
	}
	class.Size = uint32(unsafe.Sizeof(class))
	registerClass.Call(uintptr(unsafe.Pointer(&class)))
	handle, _, _ := createWindow.Call(splashExTopmost|splashExToolWindow|splashExNoActivate,
		uintptr(unsafe.Pointer(strPtr(splashClassName))), uintptr(unsafe.Pointer(strPtr(productName))),
		wsPopup, uintptr(x), uintptr(y), uintptr(w), uintptr(h), 0, 0, instance, 0)
	if handle == 0 {
		splashRelease()
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
		splashRelease()
		return
	}
	splashHandle = handle
	splashTopmost = true
	splashMutex.Unlock()
	showWindow.Call(handle, splashShowNoAct)
	updateWindow.Call(handle)
	splashSetTimer.Call(handle, splashTimerID, 16, 0)
	signal()
	var message winMessage
	for {
		result, _, _ := getMessage.Call(uintptr(unsafe.Pointer(&message)), 0, 0, 0)
		if int32(result) <= 0 {
			break
		}
		translateMessage.Call(uintptr(unsafe.Pointer(&message)))
		dispatchMessage.Call(uintptr(unsafe.Pointer(&message)))
	}
	splashRelease()
}

func splashWindowProcedure(window uintptr, message uint32, w, l uintptr) uintptr {
	switch message {
	case splashWmEraseBkgnd:
		return 1
	case splashWmPaint:
		splashPaint(window)
		return 0
	case splashWmTimer:
		splashKeepOrder(window)
		splashInvalidateIcon(window)
		return 0
	case wmClose:
		splashKillTimer.Call(window, splashTimerID)
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

func splashKeepOrder(window uintptr) {
	foreground, _, _ := splashForeground.Call()
	var owner uint32
	if foreground != 0 {
		splashWindowThread.Call(foreground, uintptr(unsafe.Pointer(&owner)))
	}
	self, _, _ := splashProcessID.Call()
	ours := foreground == 0 || uintptr(owner) == self
	if ours == splashTopmost {
		return
	}
	after := foreground
	if ours {
		after = ^uintptr(0)
	}
	setWindowPos.Call(window, after, 0, 0, 0, 0, splashNoMove|splashNoSize|splashNoActivate)
	splashTopmost = ours
}

func splashBox() rect {
	left := int32((splashWidth - splashSide) / 2)
	top := int32((splashHeight - splashSide) / 2)
	return rect{left, top, left + int32(splashSide), top + int32(splashSide)}
}

func splashInvalidateIcon(window uintptr) {
	box := splashBox()
	splashInvalidate.Call(window, uintptr(unsafe.Pointer(&box)), 0)
}

func splashEase(p float64) float64 {
	low, high := 0.0, 1.0
	for i := 0; i < 24; i++ {
		t := (low + high) / 2
		x := 3*(1-t)*(1-t)*t*0.42 + 3*(1-t)*t*t*0.58 + t*t*t
		if x < p {
			low = t
		} else {
			high = t
		}
	}
	t := (low + high) / 2
	return 3*(1-t)*t*t + t*t*t
}

func splashState() (float64, float64) {
	period := splashPulsePeriod
	if splashFade {
		period = splashFadePeriod
	}
	cycle := float64(time.Since(splashStart)%period) / float64(period)
	p := cycle * 2
	if p > 1 {
		p = 2 - p
	}
	e := splashEase(p)
	if splashFade {
		return 1, 0.6 + 0.4*e
	}
	return splashMinScale + (splashMaxScale-splashMinScale)*e, 0.7 + 0.3*e
}

func splashPaint(window uintptr) {
	ps := pixPaintStruct{}
	hdc, _, _ := pixBeginPaint.Call(window, uintptr(unsafe.Pointer(&ps)))
	if hdc == 0 {
		return
	}
	defer pixEndPaint.Call(window, uintptr(unsafe.Pointer(&ps)))
	scale, alpha := splashState()
	size := int(math.Round(float64(splashBase) * scale))
	frame, ok := splashFrames[size]
	full := rect{0, 0, int32(splashSide), int32(splashSide)}
	pixFillRect.Call(splashBuffer, uintptr(unsafe.Pointer(&full)), splashBrush)
	if ok {
		offset := (splashSide - frame.size) / 2
		blend := splashBlend{Alpha: byte(math.Round(alpha * 255)), Format: 1}
		splashAlphaBlend.Call(splashBuffer, uintptr(offset), uintptr(offset), uintptr(frame.size), uintptr(frame.size),
			frame.dc, 0, 0, uintptr(frame.size), uintptr(frame.size), *(*uintptr)(unsafe.Pointer(&blend)))
	}
	box := splashBox()
	splashBitBlt.Call(hdc, uintptr(box.Left), uintptr(box.Top), uintptr(splashSide), uintptr(splashSide), splashBuffer, 0, 0, splashSrcCopy)
	splashExcludeClip.Call(hdc, uintptr(box.Left), uintptr(box.Top), uintptr(box.Right), uintptr(box.Bottom))
	pixFillRect.Call(hdc, uintptr(unsafe.Pointer(&ps.Rectangle)), splashBrush)
}

func splashPrepare(base float64) bool {
	decoded, err := png.Decode(bytes.NewReader(splashIconPNG))
	if err != nil {
		return false
	}
	source := image.NewNRGBA(decoded.Bounds())
	draw.Draw(source, source.Bounds(), decoded, decoded.Bounds().Min, draw.Src)
	premultiplied := make([]float64, len(source.Pix))
	for i := 0; i < len(source.Pix); i += 4 {
		a := float64(source.Pix[i+3]) / 255
		premultiplied[i] = float64(source.Pix[i+2]) * a
		premultiplied[i+1] = float64(source.Pix[i+1]) * a
		premultiplied[i+2] = float64(source.Pix[i]) * a
		premultiplied[i+3] = a * 255
	}
	sw, sh := source.Bounds().Dx(), source.Bounds().Dy()
	splashBase = int(math.Round(base))
	smallest, largest := splashBase, splashBase
	if !splashFade {
		smallest = int(math.Floor(base * splashMinScale))
		largest = int(math.Ceil(base * splashMaxScale))
	}
	splashSide = largest + 2
	splashBuffer, _, _ = splashCompatibleDC.Call(0)
	reference, _, _ := splashGetDC.Call(0)
	splashBufferBM, _, _ = splashCompatBitmap.Call(reference, uintptr(splashSide), uintptr(splashSide))
	splashReleaseDC.Call(0, reference)
	splashSelect.Call(splashBuffer, splashBufferBM)
	splashFrames = map[int]splashFrame{}
	for size := smallest; size <= largest; size++ {
		if frame, ok := splashRender(premultiplied, sw, sh, size); ok {
			splashFrames[size] = frame
		}
	}
	return len(splashFrames) > 0
}

func splashRender(premultiplied []float64, sw, sh, size int) (splashFrame, bool) {
	info := splashBitmapInfo{Width: int32(size), Height: -int32(size), Planes: 1, BitCount: 32}
	info.Size = uint32(unsafe.Sizeof(info))
	var bits unsafe.Pointer
	bitmap, _, _ := splashDIBSection.Call(0, uintptr(unsafe.Pointer(&info)), 0, uintptr(unsafe.Pointer(&bits)), 0, 0)
	if bitmap == 0 || bits == nil {
		return splashFrame{}, false
	}
	pixels := unsafe.Slice((*byte)(bits), size*size*4)
	splashResample(premultiplied, sw, sh, size, pixels)
	dc, _, _ := splashCompatibleDC.Call(0)
	splashSelect.Call(dc, bitmap)
	return splashFrame{dc: dc, bitmap: bitmap, size: size}, true
}

func splashResample(premultiplied []float64, sw, sh, size int, out []byte) {
	columns := splashSpans(sw, size)
	rows := splashSpans(sh, size)
	horizontal := make([]float64, size*sh*4)
	for y := 0; y < sh; y++ {
		for x, span := range columns {
			var sum [4]float64
			for _, part := range span {
				index := (y*sw + part.index) * 4
				for c := 0; c < 4; c++ {
					sum[c] += premultiplied[index+c] * part.weight
				}
			}
			copy(horizontal[(y*size+x)*4:], sum[:])
		}
	}
	for y, span := range rows {
		for x := 0; x < size; x++ {
			var sum [4]float64
			for _, part := range span {
				index := (part.index*size + x) * 4
				for c := 0; c < 4; c++ {
					sum[c] += horizontal[index+c] * part.weight
				}
			}
			for c := 0; c < 4; c++ {
				out[(y*size+x)*4+c] = byte(math.Max(0, math.Min(255, math.Round(sum[c]))))
			}
		}
	}
}

type splashPart struct {
	index  int
	weight float64
}

func splashSpans(sourceSize, size int) [][]splashPart {
	step := float64(sourceSize) / float64(size)
	spans := make([][]splashPart, size)
	for d := 0; d < size; d++ {
		start, end := float64(d)*step, float64(d+1)*step
		if step < 1 {
			center := (start + end) / 2
			index := int(math.Min(float64(sourceSize-1), math.Floor(center)))
			spans[d] = []splashPart{{index, 1}}
			continue
		}
		for j := int(math.Floor(start)); j < int(math.Ceil(end)) && j < sourceSize; j++ {
			weight := math.Min(end, float64(j+1)) - math.Max(start, float64(j))
			if weight > 0 {
				spans[d] = append(spans[d], splashPart{j, weight / step})
			}
		}
	}
	return spans
}

func splashRelease() {
	for _, frame := range splashFrames {
		splashDeleteDC.Call(frame.dc)
		pixDeleteObject.Call(frame.bitmap)
	}
	splashFrames = nil
	if splashBuffer != 0 {
		splashDeleteDC.Call(splashBuffer)
		pixDeleteObject.Call(splashBufferBM)
		splashBuffer, splashBufferBM = 0, 0
	}
}
