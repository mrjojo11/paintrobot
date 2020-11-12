
#!/bin/bash
# A script to generate documentation and copy the necessary files to the appropriate directories
# so that the html files can be hosted on github pages.


cd docs_src
make html

cd ..
DIRECTORY=docs
if [ ! -d "$DIRECTORY" ]; then
    mkdir docs
fi

FILE=docs/.nojekyll
if [ ! -e "$FILE" ]; then
    touch docs/.nojekyll
fi

#copying built html files to docs folder to be viewed in browser
/bin/cp -r docs_src/_build/html/* docs/
/bin/rm -r docs_src/_build