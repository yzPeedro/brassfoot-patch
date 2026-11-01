package main

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	feedFileName       = "release.json"
	latestDownloadURL  = "https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/"
	releaseDownloadURL = "https://github.com/yzPeedro/brassfoot-patch/releases/download/"
	maxFeedSize        = 4 << 20
	maxAssetSize       = 256 << 20
)

type FeedAsset struct {
	Name   string `json:"name"`
	Size   int64  `json:"size"`
	SHA256 string `json:"sha256"`
}

type FeedHub struct {
	Version string               `json:"version"`
	Notes   string               `json:"notes"`
	Assets  map[string]FeedAsset `json:"assets"`
}

type ReleaseFeed struct {
	SchemaVersion int       `json:"schemaVersion"`
	Product       string    `json:"product"`
	PatchVersion  string    `json:"patchVersion"`
	PatchYear     int       `json:"patchYear"`
	Tag           string    `json:"tag"`
	Channel       string    `json:"channel"`
	PublishedAt   string    `json:"publishedAt"`
	SourceCommit  string    `json:"sourceCommit"`
	Notes         string    `json:"notes"`
	RequiresHub   string    `json:"requiresHub"`
	Bundle        FeedAsset `json:"bundle"`
	Hub           FeedHub   `json:"hub"`
}

type FeedStatus struct {
	Feed    ReleaseFeed
	Online  bool
	Cached  bool
	Loaded  bool
	Problem string
}

var (
	feedOverride  string
	feedMutex     sync.Mutex
	currentFeed   FeedStatus
	assetNamePart = regexp.MustCompile(`^[A-Za-z0-9_.-]+$`)
	sha256Pattern = regexp.MustCompile(`^[0-9a-f]{64}$`)
	feedClient    = &http.Client{Timeout: 90 * time.Second}
)

func feedIsLocal() bool {
	return feedOverride != ""
}

func cacheRoot() (string, error) {
	root, err := backupRoot()
	if err != nil {
		return "", err
	}
	return filepath.Join(filepath.Dir(root), "cache"), nil
}

func validateFeed(feed ReleaseFeed) error {
	if feed.SchemaVersion != 1 || feed.PatchVersion == "" || feed.Tag == "" {
		return errors.New("o arquivo de versão publicado está incompleto")
	}
	if !feedIsLocal() && feed.Channel != "stable" {
		return errors.New("a versão publicada não é uma release final")
	}
	if !validAsset(feed.Bundle) {
		return errors.New("o pacote da versão publicada não tem identificação válida")
	}
	for _, asset := range feed.Hub.Assets {
		if !validAsset(asset) {
			return errors.New("o instalador publicado não tem identificação válida")
		}
	}
	if !assetNamePart.MatchString(feed.Tag) {
		return errors.New("a versão publicada tem identificação inválida")
	}
	return nil
}

func validAsset(asset FeedAsset) bool {
	return assetNamePart.MatchString(asset.Name) && sha256Pattern.MatchString(asset.SHA256) &&
		asset.Size > 0 && asset.Size <= maxAssetSize
}

func readLimited(reader io.Reader, limit int64) ([]byte, error) {
	data, err := io.ReadAll(io.LimitReader(reader, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, errors.New("arquivo maior que o esperado")
	}
	return data, nil
}

func fetchURL(url string, limit int64, progress func(done, total int64)) ([]byte, error) {
	request, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	request.Header.Set("User-Agent", "BrasfootMegaPatchHub/"+hubVersion)
	response, err := feedClient.Do(request)
	if err != nil {
		return nil, fmt.Errorf("sem conexão com o GitHub: %w", err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("o GitHub respondeu %d para %s", response.StatusCode, filepath.Base(url))
	}
	if progress == nil {
		return readLimited(response.Body, limit)
	}
	var buffer bytes.Buffer
	total := response.ContentLength
	chunk := make([]byte, 64<<10)
	for {
		n, readErr := response.Body.Read(chunk)
		if n > 0 {
			buffer.Write(chunk[:n])
			if int64(buffer.Len()) > limit {
				return nil, errors.New("arquivo maior que o esperado")
			}
			progress(int64(buffer.Len()), total)
		}
		if readErr == io.EOF {
			return buffer.Bytes(), nil
		}
		if readErr != nil {
			return nil, readErr
		}
	}
}

func readFeedSource(name string, limit int64, progress func(done, total int64)) ([]byte, error) {
	if feedIsLocal() {
		file, err := os.Open(filepath.Join(feedOverride, name))
		if err != nil {
			return nil, err
		}
		defer file.Close()
		return readLimited(file, limit)
	}
	return fetchURL(latestDownloadURL+name, limit, progress)
}

func readReleaseAsset(feed ReleaseFeed, asset FeedAsset, progress func(done, total int64)) ([]byte, error) {
	if feedIsLocal() {
		file, err := os.Open(filepath.Join(feedOverride, asset.Name))
		if err != nil {
			return nil, err
		}
		defer file.Close()
		return readLimited(file, asset.Size)
	}
	return fetchURL(releaseDownloadURL+feed.Tag+"/"+asset.Name, asset.Size, progress)
}

func fetchFeed() (ReleaseFeed, error) {
	var feed ReleaseFeed
	body, err := readFeedSource(feedFileName, maxFeedSize, nil)
	if err != nil {
		return feed, err
	}
	if err = json.Unmarshal(body, &feed); err != nil {
		return feed, fmt.Errorf("arquivo de versão inválido: %w", err)
	}
	if err = validateFeed(feed); err != nil {
		return feed, err
	}
	if root, rootErr := cacheRoot(); rootErr == nil && !feedIsLocal() {
		if os.MkdirAll(root, 0700) == nil {
			_ = os.WriteFile(filepath.Join(root, feedFileName), body, 0600)
		}
	}
	return feed, nil
}

func cachedFeed() (ReleaseFeed, error) {
	var feed ReleaseFeed
	root, err := cacheRoot()
	if err != nil {
		return feed, err
	}
	body, err := os.ReadFile(filepath.Join(root, feedFileName))
	if err != nil {
		return feed, err
	}
	if err = json.Unmarshal(body, &feed); err != nil {
		return feed, err
	}
	return feed, validateFeed(feed)
}

func cachedAssetPath(asset FeedAsset) (string, error) {
	root, err := cacheRoot()
	if err != nil {
		return "", err
	}
	return filepath.Join(root, asset.SHA256+filepath.Ext(asset.Name)), nil
}

func verifiedAsset(data []byte, asset FeedAsset) error {
	if int64(len(data)) != asset.Size || digestBytes(data) != asset.SHA256 {
		return fmt.Errorf("o arquivo %s baixado não confere com o SHA-256 publicado", asset.Name)
	}
	return nil
}

func loadAsset(feed ReleaseFeed, asset FeedAsset, offline bool, progress func(done, total int64)) ([]byte, error) {
	path, pathErr := cachedAssetPath(asset)
	if pathErr == nil {
		if data, err := os.ReadFile(path); err == nil && verifiedAsset(data, asset) == nil {
			return data, nil
		}
	}
	if offline {
		return nil, errors.New("sem conexão e sem cópia guardada desta versão")
	}
	data, err := readReleaseAsset(feed, asset, progress)
	if err != nil {
		return nil, err
	}
	if err = verifiedAsset(data, asset); err != nil {
		return nil, err
	}
	if pathErr == nil && !feedIsLocal() {
		if os.MkdirAll(filepath.Dir(path), 0700) == nil {
			temporary := path + ".part"
			if os.WriteFile(temporary, data, 0600) == nil {
				_ = os.Remove(path)
				_ = os.Rename(temporary, path)
			}
		}
	}
	return data, nil
}

func bundleFromZip(data []byte, feed ReleaseFeed) (fs.FS, error) {
	reader, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return nil, fmt.Errorf("pacote da versão inválido: %w", err)
	}
	for _, file := range reader.File {
		if !strings.HasPrefix(file.Name, "bundled_release/") || strings.Contains(file.Name, "..") {
			return nil, errors.New("pacote da versão contém caminhos inesperados")
		}
	}
	body, err := fs.ReadFile(reader, "bundled_release/manifest.json")
	if err != nil {
		return nil, errors.New("pacote da versão sem manifesto")
	}
	var manifest Manifest
	if err = json.Unmarshal(body, &manifest); err != nil {
		return nil, fmt.Errorf("manifesto do pacote inválido: %w", err)
	}
	if manifest.Version != feed.PatchVersion || len(manifest.Files) == 0 {
		return nil, errors.New("o pacote baixado não corresponde à versão publicada")
	}
	if !feedIsLocal() && (!manifest.PublicationAllowed || manifest.Kind != "BRASFOOT_RELEASE_PATCH") {
		return nil, errors.New("o pacote baixado não é uma release final")
	}
	return reader, nil
}

func refreshFeed(progress func(done, total int64)) FeedStatus {
	status := FeedStatus{}
	feed, err := fetchFeed()
	if err == nil {
		status.Feed = feed
		status.Online = true
	} else {
		status.Problem = err.Error()
		if feedIsLocal() {
			setFeedStatus(status)
			return status
		}
		cached, cacheErr := cachedFeed()
		if cacheErr != nil {
			setFeedStatus(status)
			return status
		}
		status.Feed = cached
		status.Cached = true
	}
	if compareVersions(coreVersion(hubVersion), status.Feed.RequiresHub) < 0 {
		status.Problem = "esta versão do patch precisa do instalador " + status.Feed.RequiresHub + " ou mais novo"
		setFeedStatus(status)
		return status
	}
	data, err := loadAsset(status.Feed, status.Feed.Bundle, !status.Online, progress)
	if err != nil {
		status.Problem = err.Error()
		setFeedStatus(status)
		return status
	}
	payload, err := bundleFromZip(data, status.Feed)
	if err != nil {
		status.Problem = err.Error()
		setFeedStatus(status)
		return status
	}
	setPayload(payload)
	status.Loaded = true
	setFeedStatus(status)
	return status
}

func setFeedStatus(status FeedStatus) {
	feedMutex.Lock()
	currentFeed = status
	feedMutex.Unlock()
}

func feedStatus() FeedStatus {
	feedMutex.Lock()
	defer feedMutex.Unlock()
	return currentFeed
}

func hubAssetKey() string {
	platform := runtime.GOOS
	if platform == "darwin" {
		platform = "macos"
	}
	architecture := "x64"
	if runtime.GOARCH == "arm64" {
		architecture = "arm64"
	}
	return platform + "-" + architecture
}

func hubUpdateAvailable(feed ReleaseFeed) bool {
	_, ok := feed.Hub.Assets[hubAssetKey()]
	return ok && feed.Hub.Version != "" && compareVersions(feed.Hub.Version, hubVersion) > 0
}

func coreVersion(value string) string {
	core, _, _ := strings.Cut(strings.TrimSpace(value), "-")
	return core
}

func versionParts(value string) ([]int, string) {
	value = strings.TrimPrefix(strings.TrimSpace(value), "v")
	core, pre, _ := strings.Cut(value, "-")
	parts := []int{}
	for _, piece := range strings.Split(core, ".") {
		number, err := strconv.Atoi(piece)
		if err != nil {
			number = 0
		}
		parts = append(parts, number)
	}
	return parts, pre
}

func compareVersions(a, b string) int {
	if strings.TrimSpace(b) == "" {
		return 1
	}
	if strings.TrimSpace(a) == "" {
		return -1
	}
	left, leftPre := versionParts(a)
	right, rightPre := versionParts(b)
	for i := 0; i < len(left) || i < len(right); i++ {
		l, r := 0, 0
		if i < len(left) {
			l = left[i]
		}
		if i < len(right) {
			r = right[i]
		}
		if l != r {
			if l < r {
				return -1
			}
			return 1
		}
	}
	switch {
	case leftPre == rightPre:
		return 0
	case leftPre == "":
		return 1
	case rightPre == "":
		return -1
	case leftPre < rightPre:
		return -1
	default:
		return 1
	}
}
