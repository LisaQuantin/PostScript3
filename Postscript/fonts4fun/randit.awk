#$Id: randit.awk,v 1.18 2002/12/29 20:42:32 hahe Exp hahe $
# Hack for Randomizing cm***.pfb Font
# H. Henkel, 24.12.2002
# In the public domain, no warranty, use on your own risk. 

function hrand(x, mh, ah){
  if (x > 0)
    return int(x * (1 + mh * (rand() - 0.5)) + ah * (rand() - 0.5) + 0.5);
  else
    return -int(-x * (1 + mh * (rand() - 0.5)) + ah * (rand() - 0.5) + 0.5);
}

function vrand(y, mv, av){
  if (y > 0)
    return int(y * (1 + mv * (rand() - 0.5)) + av * (rand() - 0.5) + 0.5);
  else
    return -int(-y * (1 + mv * (rand() - 0.5)) + av * (rand() - 0.5) + 0.5);
}

BEGIN{
  fmh = 0.0;	# first move, multiplicative
  fmv = 0.0;
  fah = 10;	# additive
  fav = 40;
  mh = 0;	# all others, multiplicative
  mv = 0;
  ah = 30;	# additive
  av = 30;
  linesonly = 0;	# replace curves by straight lines
#  srand(0);	# for reproducible random result
}

/[0-9-][0-9]*  *[0-9-][0-9]*  *.stem/ {next}	# no hinting

/{/ {
  firstmoveto = 1;
}

/hmoveto/ {sub($1, "& 0"); sub($3, "rmoveto");}
/vmoveto/ {sub($1, "0 &"); sub($3, "rmoveto");}

/rmoveto/ {
  if (firstmoveto)
    print hrand($1, fmh, fah), vrand($2, fmv, fav), $3;
  else
    print hrand($1, mh, ah), vrand($2, mv, av), $3;
  firstmoveto = 0;
  next;
}

/hlineto/ { sub($1, "& 0"); sub($3, "rlineto"); }
/vlineto/ { sub($1, "0 &"); sub($3, "rlineto"); }

/rlineto/ {
  print hrand($1, mh, ah), vrand($2, mv, av), $3;
  next;
}

/hvcurveto/ {
# x1 0 x2 y2 0 y3 rrcurveto
  sub($1, "& 0");
  sub($5, "0 &");
  sub($7, "rrcurveto");
}

/vhcurveto/ {
# 0 y1 x2 y2 x3 0 rrcurveto
  sub($1, "0 &");
  sub($5, "& 0");
  sub($7, "rrcurveto");
}

/rrcurveto/ {
  if(linesonly) {
    print hrand($1, mh, ah), vrand($2, mv, av), "rlineto";
    print hrand($3, mh, ah), vrand($4, mv, av), "rlineto";
    print hrand($5, mh, ah), vrand($6, mv, av), "rlineto";
  } else {
    print hrand($1, mh, ah), vrand($2, mv, av), \
    hrand($3, mh, ah), vrand($4, mv, av), \
    hrand($5, mh, ah), vrand($6, mv, av), $7;
  }
  next;
}

/.*/ { print}
