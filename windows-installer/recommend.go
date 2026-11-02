package main

import (
	"encoding/binary"
	"errors"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

const (
	liveMinimumMemory = 4 << 30
	liveMinimumCores  = 3
	liveFastestSpeed  = 3
)

type Recommendation struct {
	Speed       int             `json:"speed"`
	SpeedKnown  bool            `json:"speedKnown"`
	Careers     []string        `json:"careers"`
	MemoryBytes uint64          `json:"memoryBytes"`
	Cores       int             `json:"cores"`
	LowHardware bool            `json:"lowHardware"`
	FastSpeed   bool            `json:"fastSpeed"`
	Components  map[string]bool `json:"components"`
}

func recommendFor(game string) Recommendation {
	r := Recommendation{Speed: -1, Cores: runtime.NumCPU(), MemoryBytes: installedMemory()}
	if speed, err := readGameSpeed(filepath.Join(game, "options.bcf")); err == nil {
		r.Speed, r.SpeedKnown = speed, true
	}
	r.Careers = savedCareers(game)
	r.LowHardware = (r.MemoryBytes > 0 && r.MemoryBytes < liveMinimumMemory) || r.Cores < liveMinimumCores
	r.FastSpeed = r.SpeedKnown && r.Speed > liveFastestSpeed
	r.Components = map[string]bool{
		componentRosters: true,
		componentSeason:  true,
		componentLive:    !r.LowHardware && !r.FastSpeed,
		componentCrests:  true,
	}
	return r
}

func savedCareers(game string) []string {
	entries, err := os.ReadDir(filepath.Join(game, "sav"))
	if err != nil {
		return []string{}
	}
	careers := []string{}
	for _, entry := range entries {
		name := entry.Name()
		if entry.Type().IsRegular() && strings.EqualFold(filepath.Ext(name), ".s22") {
			careers = append(careers, strings.TrimSuffix(name, filepath.Ext(name)))
		}
	}
	sort.Strings(careers)
	return careers
}

func readGameSpeed(path string) (int, error) {
	body, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}
	if len(body) > 64*1024 {
		return 0, errors.New("options.bcf grande demais")
	}
	p := 0
	need := func(n int) bool { return p+n <= len(body) }
	u16 := func() int {
		value := int(binary.BigEndian.Uint16(body[p:]))
		p += 2
		return value
	}
	if !need(6) || binary.BigEndian.Uint32(body) != 0xaced0005 || body[4] != 0x73 || body[5] != 0x72 {
		return 0, errors.New("options.bcf em formato desconhecido")
	}
	p = 6
	if !need(2) {
		return 0, errors.New("options.bcf truncado")
	}
	nameLength := u16()
	if !need(nameLength+11) || string(body[p:p+nameLength]) != "est.Options" {
		return 0, errors.New("options.bcf de outra classe")
	}
	p += nameLength + 9
	count := u16()
	type field struct {
		kind byte
		name string
	}
	fields := make([]field, 0, count)
	for i := 0; i < count; i++ {
		if !need(3) {
			return 0, errors.New("options.bcf truncado")
		}
		kind := body[p]
		p++
		length := u16()
		if !need(length) {
			return 0, errors.New("options.bcf truncado")
		}
		name := string(body[p : p+length])
		p += length
		if kind == '[' || kind == 'L' {
			if !need(1) {
				return 0, errors.New("options.bcf truncado")
			}
			switch body[p] {
			case 0x74:
				p++
				if !need(2) {
					return 0, errors.New("options.bcf truncado")
				}
				p += u16()
			case 0x71:
				p += 5
			default:
				return 0, errors.New("options.bcf em formato desconhecido")
			}
		}
		fields = append(fields, field{kind, name})
	}
	if !need(2) || body[p] != 0x78 || body[p+1] != 0x70 {
		return 0, errors.New("options.bcf em formato desconhecido")
	}
	p += 2
	sizes := map[byte]int{'Z': 1, 'B': 1, 'C': 2, 'S': 2, 'I': 4, 'F': 4, 'J': 8, 'D': 8}
	for _, f := range fields {
		size, primitive := sizes[f.kind]
		if !primitive || !need(size) {
			break
		}
		if f.name == "velocidade" && f.kind == 'I' {
			speed := int(int32(binary.BigEndian.Uint32(body[p:])))
			if speed < 0 || speed > 5 {
				return 0, errors.New("velocidade fora da faixa")
			}
			return speed, nil
		}
		p += size
	}
	return 0, errors.New("velocidade não encontrada")
}
