#! /usr/bin/sh

#$1: VERSION
#$2: RELEASE
#$3: DATE
#$4: LONG_COMMIT

if [ -z $4 ]
then
    if [ -z $2 ]
    then
        echo -en "Usage: \e[0;32mbuild-rpm\e[1;33m VERSION RELEASE \e[m[\e[1;33m DATE COMMIT\e[m ]\n"
        exit 1
    else
        echo "release"
        VERSION=$1
        RELEASE=$2
        
        REL_BUILD=1
        
        sed -e 's/VERSION/'$VERSION'/g' -e 's/RELEASE/'$RELEASE'/g' -e 's/^#global rel_build 1/%global rel_build 1/g' spicegui.spec.template > ~/rpmbuild/SPECS/spicegui.spec
        wget -O ~/rpmbuild/SOURCES/spicegui-$VERSION.tar.gz  https://github.com/rafael1193/spicegui/archive/v$VERSION.tar.gz
        rpmbuild -ba ~/rpmbuild/SPECS/spicegui.spec
        
        exit 0
    fi
else
    VERSION=$1
    RELEASE=$2
    DATE=$3
    LONG_COMMIT=$4
    SHORT_COMMIT=$(expr substr $LONG_COMMIT 1 7)
    
    REL_BUILD=0

    sed -e 's/VERSION/'$VERSION'/g' -e 's/RELEASE/'$RELEASE'/g' -e 's/LONG_COMMIT/'$LONG_COMMIT'/g' -e 's/DATE/'$DATE'/g' -e 's/REL_BUILD/'$REL_BUILD'/g' spicegui.spec.template > ~/rpmbuild/SPECS/spicegui.spec
    wget -O ~/rpmbuild/SOURCES/spicegui-$VERSION-git$DATE-$SHORT_COMMIT.tar.gz  https://github.com/rafael1193/spicegui/archive/$LONG_COMMIT.tar.gz
    rpmbuild -ba ~/rpmbuild/SPECS/spicegui.spec
    
    exit 0
fi

