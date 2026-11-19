package main

import "fmt"

const (
	maxBundleFiles      = 16384
	maxManifestBytes    = 16 << 20
	maxBundleFileBytes  = 25 << 20
	maxBundleTotalBytes = int64(2) << 30
)

func validateManifestLimits(files []ManifestFile) error {
	if len(files) < 1 || len(files) > maxBundleFiles {
		return fmt.Errorf("o pacote precisa ter de 1 a %d arquivos autorizados; encontrados %d", maxBundleFiles, len(files))
	}
	var total int64
	for _, f := range files {
		if f.Size < 4 || f.Size > maxBundleFileBytes {
			return fmt.Errorf("tamanho inválido no pacote: %s", f.Path)
		}
		total += f.Size
		if total > maxBundleTotalBytes {
			return fmt.Errorf("o pacote passa de %d bytes somando os arquivos", maxBundleTotalBytes)
		}
	}
	return nil
}
