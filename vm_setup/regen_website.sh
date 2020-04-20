#!/bin/bash
shopt -s extglob
shopt -s nullglob

~/website/gen_page.py ~/reports/*.json
