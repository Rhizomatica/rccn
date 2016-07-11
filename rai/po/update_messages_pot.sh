#!/bin/bash
cp messages.pot messages.pot.bak
xgettext --files-from=POTFILES.in --directory=.. --output=messages.pot
