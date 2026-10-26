//go:build windows

package main

import (
    "encoding/base64"
    "fmt"
    "syscall"
    "unsafe"
)

// Diálogo nativo: não abre navegador, não cria cobrança nem impede a
// instalação. As ações de Pix só são executadas após clique do usuário.
const (
    pixWindowClass = "BrassfootPatchPixDialog2026"
    pixCopyID = 411
    wmPaintPix = 0x000F
    wmCopyText = 0x0301
    emSetSel = 0x00B1
    esMultiline = 0x0004
    esReadOnly = 0x0800
    wsVScroll = 0x00200000
)

var (
    pixWindow uintptr
    pixCodeControl uintptr
    pixCopyStatus uintptr
    pixClassRegistered bool
    pixBytes []byte
    pixBeginPaint = u32.NewProc("BeginPaint")
    pixEndPaint = u32.NewProc("EndPaint")
    pixDestroyWindow = u32.NewProc("DestroyWindow")
    pixFillRect = u32.NewProc("FillRect")
    pixDeleteObject = g32.NewProc("DeleteObject")
    pixForeground = u32.NewProc("SetForegroundWindow")
)

type pixPaintStruct struct {
    Hdc uintptr
    Erase int32
    Rectangle rect
    Restore int32
    Incremental int32
    Reserved [32]byte
}

func pixControl(parent uintptr, class, title string, style uintptr, x, y, w, h int, ident int, font uintptr) uintptr {
    instance, _, _ := getModule.Call(0)
    handle, _, _ := createWindow.Call(0,
        uintptr(unsafe.Pointer(strPtr(class))), uintptr(unsafe.Pointer(strPtr(title))),
        style, uintptr(x), uintptr(y), uintptr(w), uintptr(h),
        parent, uintptr(ident), instance, 0)
    if handle != 0 && font != 0 { sendMessage.Call(handle,wmSetFont,font,1) }
    return handle
}

func pixDraw(h uintptr) {
    ps := pixPaintStruct{}
    hdc, _, _ := pixBeginPaint.Call(h,uintptr(unsafe.Pointer(&ps)))
    if hdc == 0 { return }
    defer pixEndPaint.Call(h,uintptr(unsafe.Pointer(&ps)))
    background,_,_:=newBrush.Call(color(255,255,255))
    foreground,_,_:=newBrush.Call(color(0,0,0))
    defer pixDeleteObject.Call(background)
    defer pixDeleteObject.Call(foreground)
    const step int32 = 4
    const left int32 = 93
    const top int32 = 72
    region:=rect{Left:left,Top:top,Right:left+65*step,Bottom:top+65*step}
    pixFillRect.Call(hdc,uintptr(unsafe.Pointer(&region)),background)
    for y:=0;y<pixQRSize;y++ {
        for x:=0;x<pixQRSize;x++ {
            offset:=y*pixQRSize+x
            if pixBytes[offset/8]&(1<<uint(7-offset%8))==0 { continue }
            block:=rect{Left:left+int32(x)*step,Top:top+int32(y)*step,
                Right:left+int32(x+1)*step,Bottom:top+int32(y+1)*step}
            pixFillRect.Call(hdc,uintptr(unsafe.Pointer(&block)),foreground)
        }
    }
}

func pixWindowProc(h uintptr, message uint32, w,l uintptr) uintptr {
    switch message {
    case wmCreate:
        pixWindow=h
        white:=color(238,246,237)
        muted:=color(177,197,185)
        first:=pixControl(h,"STATIC","Apoie com um cafezinho ☕",wsVisible|wsChild,21,16,382,30,0,strongFont)
        labelColors[first]=white
        second:=pixControl(h,"STATIC","100% opcional. O patch continua gratuito.",wsVisible|wsChild,22,45,383,24,0,smallFont)
        labelColors[second]=muted
        third:=pixControl(h,"STATIC","Pix copia e cola (sem valor definido):",wsVisible|wsChild,21,342,383,24,0,smallFont)
        labelColors[third]=white
        pixCodeControl=pixControl(h,"EDIT",pixPayload,wsVisible|wsChild|wsBorder|esMultiline|esReadOnly|wsVScroll,
            21,368,385,63,0,smallFont)
        pixControl(h,"BUTTON","COPIAR CÓDIGO PIX",wsVisible|wsChild|wsTabStop,21,442,214,38,pixCopyID,bodyFont)
        pixCopyStatus=pixControl(h,"STATIC","Sem cobrança, cadastro ou rastreamento.",wsVisible|wsChild,21,491,390,26,0,smallFont)
        labelColors[pixCopyStatus]=muted
        return 0
    case wmPaintPix:
        pixDraw(h)
        return 0
    case wmCommand:
        if int(w&0xffff)==pixCopyID && pixCodeControl!=0 {
            sendMessage.Call(pixCodeControl,emSetSel,0,^uintptr(0))
            sendMessage.Call(pixCodeControl,wmCopyText,0,0)
            setText(pixCopyStatus,"Código Pix copiado. Obrigado por apoiar!")
            return 0
        }
    case wmCtlColorStatic:
        setBkMode.Call(w,colorTransparent)
        tint,ok:=labelColors[l]
        if !ok { tint=color(whiteR,whiteG,whiteB) }
        setTextColor.Call(w,tint)
        return darkBrush
    case wmClose:
        pixDestroyWindow.Call(h)
        return 0
    case wmDestroy:
        pixWindow=0
        pixCodeControl=0
        pixCopyStatus=0
        enableWindow.Call(hwnd,1)
        pixForeground.Call(hwnd)
        return 0
    }
    ret,_,_:=defWindow.Call(h,uintptr(message),w,l)
    return ret
}

func showPixDialog() {
    if pixWindow!=0 {
        pixForeground.Call(pixWindow)
        return
    }
    if pixBytes==nil {
        data,err:=base64.StdEncoding.DecodeString(pixQRBitsBase64)
        if err!=nil || len(data)!=(pixQRSize*pixQRSize+7)/8 {
            msgbox("O QR Code Pix não passou na verificação. Não houve qualquer cobrança.","Pix indisponível",mbOK|mbIconWarning)
            return
        }
        pixBytes=data
    }
    if !pixClassRegistered {
        inst,_,_:=getModule.Call(0)
        class:=winClass{Size:uint32(unsafe.Sizeof(winClass{})),Procedure:syscall.NewCallback(pixWindowProc),
            Instance:inst,Background:darkBrush,ClassName:strPtr(pixWindowClass)}
        if ok,_,err:=registerClass.Call(uintptr(unsafe.Pointer(&class)));ok==0 {
            msgbox(fmt.Sprintf("Não foi possível abrir o diálogo Pix: %v",err),"Pix opcional",mbOK|mbIconWarning)
            return
        }
        pixClassRegistered=true
    }
    inst,_,_:=getModule.Call(0)
    popup,_,_:=createWindow.Call(0,uintptr(unsafe.Pointer(strPtr(pixWindowClass))),
        uintptr(unsafe.Pointer(strPtr("Brasfoot Patch — Pix voluntário"))),
        wsCaption|wsSysMenu|wsVisible,220,130,438,578,hwnd,0,inst,0)
    if popup==0 {
        msgbox("Não foi possível mostrar o Pix. O instalador continua gratuito.","Pix opcional",mbOK|mbIconWarning)
        return
    }
    pixWindow=popup
    enableWindow.Call(hwnd,0)
    showWindow.Call(popup,swShow)
    updateWindow.Call(popup)
}
