#$Id: t1tomp.awk,v 1.5 2002/12/29 20:42:32 hahe Exp hahe $
# Hack for Conversion of cm***.pfb Font into MetaPost
# H. Henkel, 24.12.2002
# In the public domain, no warranty, use on your own risk. 

function dotit (x,y) {
  printf("draw (%d,%d) withpen pencircle scaled 4mm;\n", x, y);
}

function sqdotit (x,y) {
  printf("fill unitsquare scaled 4mm shifted (-2mm,-2mm) shifted (%d,%d);\n", x, y);
}

BEGIN {
  letteractive = 0;
  print "paperheight = sqrt(sqrt(2)) * 1000mm / 4;";
  print "paperwidth = paperheight / sqrt(2);";
  print "def withblue = withpen pencircle scaled 2mm withcolor blue enddef;";
  print "def withred = withpen pencircle scaled 2mm withcolor red enddef;";
  print "def withblack = withpen pencircle scaled 2mm enddef;";
}

/^dup  *[0-9][0-9]*  *.*  *put *$/ {
  i = $2 + 0;
  f[$3] = i;
}

/.stem/ {
  next;
}

/rmoveto/ {
  if (letteractive) {
    x = $1 + 0 + x;
    y = $2 + 0 + y;
    xs = x;
    ys = y;
  }
}

/hmoveto/ {
  if (letteractive) {
    x = $1 + 0 + x;
    xs = x;
    ys = y;
  }
}

/vmoveto/ {
  if (letteractive) {
    y = $1 + 0 + y;
    xs = x;
    ys = y;
  }
}

/rlineto/ {
  if (letteractive) {
    dx = $1 + 0;
    dy = $2 + 0;
    printf("draw (%d,%d)--(%d,%d) withblue;\n", x, y, x + dx, y + dy);
    x = x + dx;
    y = y + dy;
    dotit(x,y);
  }
}

/hlineto/ {
  if (letteractive) {
    dx = $1 + 0;
    printf("draw (%d,%d)--(%d,%d) withblue;\n", x, y, x + dx, y);
    x = x + dx;
    dotit(x,y);
  }
}

/vlineto/ {
  if (letteractive) {
    dy = $1 + 0;
    printf("draw (%d,%d)--(%d,%d) withblue;\n", x, y, x, y + dy);
    y = y + dy;
    dotit(x,y);
  }
}

/rrcurveto/ {
  if (letteractive) {
    x1 = $1 + 0 + x;
    y1 = $2 + 0 + y;
    x2 = $3 + 0 + x1;
    y2 = $4 + 0 + y1;
    x3 = $5 + 0 + x2;
    y3 = $6 + 0 + y2;
    printf("draw (%d,%d)..controls(%d,%d)and(%d,%d)..(%d,%d) withred;\n", x, y, x1, y1, x2, y2, x3, y3);
    x = x3;
    y = y3;
    dotit(x,y);
  }
}

/hvcurveto/ {
  if (letteractive) {
    x1 = $1 + 0 + x;
    y1 = 0 + y;
    x2 = $2 + 0 + x1;
    y2 = $3 + 0 + y1;
    x3 = 0 + x2;
    y3 = $4 + 0 + y2;
    printf("draw (%d,%d)..controls(%d,%d)and(%d,%d)..(%d,%d) withred;\n", x, y, x1, y1, x2, y2, x3, y3);
    x = x3;
    y = y3;
    dotit(x,y);
  }
}

/vhcurveto/ {
  if (letteractive) {
    x1 = 0 + x;
    y1 = $1 + 0 + y;
    x2 = $2 + 0 + x1;
    y2 = $3 + 0 + y1;
    x3 = $4 + 0 + x2;
    y3 = 0 + y2;
    printf("draw (%d,%d)..controls(%d,%d)and(%d,%d)..(%d,%d) withred;\n", x, y, x1, y1, x2, y2, x3, y3);
    x = x3;
    y = y3;
    dotit(x,y);
  }
}

/closepath/ {
  if (letteractive) {
    printf("draw (%d,%d)--(%d,%d) withblack;\n", x, y, xs, ys);
    sqdotit(xs,ys);
  }
}

/^\/[A-Za-z][A-Za-z]* {/ {
  if(f[$1] >= 0) {
    letter = f[$1];
    letteractive = 1;
    x = 0;
    y = 0;
    printf("beginfig(%d) %% %s;\n", letter, $1);
    printf("draw origin--500right;\n");
  }
}

/} ND/ {
  if (letteractive) {
    print "currentpicture := currentpicture";
    print "  scaled 0.3;";
    print "currentpicture := currentpicture";
    print "  shifted -0.5[llcorner currentpicture, urcorner currentpicture]";
    print "  shifted 0.5(paperwidth, paperheight);";
    print "endfig;"
    letteractive = 0;
  }
}

END {
  print "end;"
}
