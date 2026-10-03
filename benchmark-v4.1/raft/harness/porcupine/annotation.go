package porcupine

// Annotation is retained from upstream porcupine only as a type referenced by
// LinearizationInfo. The HTML visualization machinery (and its embedded assets)
// is intentionally NOT vendored: the grader is a pure in-process linearizability
// checker and never renders a visualization.
type Annotation struct {
	ClientId        int
	Tag             string
	Start           int64
	End             int64
	Description     string
	Details         string
	TextColor       string
	BackgroundColor string
	_               struct{} // disallow positional literals, for extensibility
}
