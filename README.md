# PostScript3
Testing the creation of a PostScript Type 3 font for the PSAT project.

### Lancement 

`npm init -y`
`npm install opentype.js`
`node main.js`

### Method

Using the opentype.js library in JavaScript/Node to try and create a personalized and randomized font.

CAUTION : opentype.js create modern font, in .otf, whereas PostScript3 should be a .pfa. We can use fontforge to modify formats.

### What Lisa is trying to do
- 23/10 : Creation f a first font, based on svg of my writing
- 15/10 : Creation of letter a and font

### To Improve

- Add random : for now, glyphs repet in a cycle and not randomly (so that conventional writing software can use the font)
- Add noise : forcing X glyphes per letter, maybe by adding noise ? 

### Docs
- https://www.npmjs.com/package/opentype.js
- https://fontforge.org/docs/index.html
