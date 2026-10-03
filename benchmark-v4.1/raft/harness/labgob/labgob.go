// Package labgob is a tiny clean-room wrapper around encoding/gob.
//
// It exists so the rest of the harness has a single, explicit encoding
// surface (and so later sprints can add warnings about non-capitalized
// struct fields, default-value traps, etc. in one place). It is NOT a copy
// of any course's labgob; it is a thin, obvious shim over the stdlib.
package labgob

import (
	"encoding/gob"
	"io"
	"reflect"
	"sync"
)

// Encoder wraps a gob.Encoder.
type Encoder struct {
	g *gob.Encoder
}

// NewEncoder returns an Encoder writing to w.
func NewEncoder(w io.Writer) *Encoder {
	return &Encoder{g: gob.NewEncoder(w)}
}

// Encode encodes a value (or pointer to a value).
func (e *Encoder) Encode(v interface{}) error {
	return e.g.Encode(v)
}

// EncodeValue encodes a reflect.Value.
func (e *Encoder) EncodeValue(v reflect.Value) error {
	return e.g.EncodeValue(v)
}

// Decoder wraps a gob.Decoder.
type Decoder struct {
	g *gob.Decoder
}

// NewDecoder returns a Decoder reading from r.
func NewDecoder(r io.Reader) *Decoder {
	return &Decoder{g: gob.NewDecoder(r)}
}

// Decode decodes into the value pointed at by v.
func (d *Decoder) Decode(v interface{}) error {
	return d.g.Decode(v)
}

// DecodeValue decodes into the addressable reflect.Value v.
func (d *Decoder) DecodeValue(v reflect.Value) error {
	return d.g.DecodeValue(v)
}

var regMu sync.Mutex

// Register makes a concrete type transmissible when stored in an interface{}
// field (e.g. a Raft command). Safe to call repeatedly with the same type.
func Register(value interface{}) {
	regMu.Lock()
	defer regMu.Unlock()
	gob.Register(value)
}

// RegisterName is Register with an explicit name.
func RegisterName(name string, value interface{}) {
	regMu.Lock()
	defer regMu.Unlock()
	gob.RegisterName(name, value)
}

func init() {
	// Command values in the foundation tests are ints; register eagerly so
	// encoding an int inside an interface{} never trips over registration.
	gob.Register(0)
	gob.Register("")
}
