#!/bin/bash

rm postscript.pdf

ps2pdf postscript.ps

open postscript.pdf 2>/dev/null