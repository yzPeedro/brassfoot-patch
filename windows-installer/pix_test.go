package main

import (
    "encoding/base64"
    "strings"
    "testing"
)

func pixCRC16(data []byte) uint16 {
    var crc uint16 = 0xFFFF
    for _, value := range data {
        crc ^= uint16(value) << 8
        for i:=0;i<8;i++ {
            if crc&0x8000 != 0 { crc = (crc<<1)^0x1021 } else { crc <<= 1 }
        }
    }
    return crc
}

func TestPixPayloadCRCAndNoFixedValue(t *testing.T) {
    if len(pixPayload)<8 || !strings.HasSuffix(pixPayload,"630482B0") { t.Fatal("unexpected EMV payload") }
    check := pixPayload[:len(pixPayload)-4]
    if actual:=pixCRC16([]byte(check)); actual!=0x82B0 { t.Fatalf("CRC Pix inválido: %04X", actual) }
    if strings.Contains(pixPayload,"540") { t.Fatal("Pix não deve estabelecer valor obrigatório") }
    if !strings.Contains(pixPayload,"dd20e247-c861-44a1-9a21-2ddb827465e9") { t.Fatal("Pix key was changed") }
}

func TestPixQRCodeMatrixHasQuietZoneAndFinderPatterns(t *testing.T) {
    data,err:=base64.StdEncoding.DecodeString(pixQRBitsBase64)
    if err!=nil || len(data)!=(pixQRSize*pixQRSize+7)/8 { t.Fatalf("invalid QR bit matrix: %v",err) }
    bit:=func(x,y int) bool {
        i:=y*pixQRSize+x
        return data[i/8]&(1<<uint(7-i%8))!=0
    }
    for i:=0;i<pixQRSize;i++ {
        for j:=0;j<4;j++ {
            if bit(i,j)||bit(j,i)||bit(i,pixQRSize-1-j)||bit(pixQRSize-1-j,i) {
                t.Fatal("missing QR quiet zone")
            }
        }
    }
    for _,p:=range [][2]int{{4,4},{54,4},{4,54}} {
        if !bit(p[0],p[1])||!bit(p[0]+6,p[1])||!bit(p[0],p[1]+6)||!bit(p[0]+6,p[1]+6) {
            t.Fatal("QR finder markers missing")
        }
    }
}
