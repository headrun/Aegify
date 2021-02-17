#!/bin/sh

. $(dirname "$0")/base.sh

validate() {
    branchName=$2
    defaultHeadOrigin="origin/HEAD"

    if [ "$branchName" != "master" ]
    then
        defaultHeadOrigin=$branchName
    fi

    echo "Tag was released on $branchName Branch"

    v=`git diff $defaultHeadOrigin $1 | head -n 1`
    if [ "$v" != "" ]
    then
        echo "Error: Uncommited local changes. run git status; git log --decorate --oneline"
        exit 1
    fi
}

create_and_push_tag() {
    name=$1

    git tag -a $name -m "Releasing $name"
    git push origin $name
}

create_release_dir() {
    rel_dir=$1
    files=$2

    rm -rf $rel_dir

    for x in $files
    do
        d=$rel_dir/$(dirname $x)
        mkdir -p $d
        cp $x $d/
    done
}

main() {
    release_root=$1
    tag_name=$2
    if [ -z $release_root ] || [ ! -d $release_root ]
    then
        echo "Invalid arguments. release.sh <path_for_releases>"
        exit 1
    fi

    base_validate
    sites_dir="sites/$SITE"
    if [ ! -d "$sites_dir" ]
    then
        echo "SITE=<$SITE> is not present in sites."
        exit 1
    fi

    dirs="deploy $sites_dir manage.py scrapy.cfg sites/__init__.py `$pyt -c \"from sites.$SITE import DEPLOY_DIRS; print(' '.join(DEPLOY_DIRS))\"`"

    files=`git ls-files $dirs | grep '.\(py\|sh\|cfg\|conf\|ini\|md\|js\|html\|css\|jpg\|png\|json\)$' | grep -v pylint.sh`

    branch=`git branch -v | grep '^*' | cut -f2 -d' '`
    validate "$files" $branch

    if [ -z $tag_name ]
    then
        commit=`git log --format="%h" -n 1`
        if [ ${branch} = "master" ]
        then
            branch=${g_project}
        fi
        release_dir=${branch}-$SITE-${commit}-${g_timestamp}
    else
        release_dir=${tag_name}
        create_and_push_tag $release_dir
    fi

    cd $g_project_dir
    create_release_dir $release_root/$release_dir "$files"

    cd $release_root
    tar -czf $release_dir.tgz $release_dir
    rm -rf $release_dir
    echo "Release: $PWD/${release_dir}.tgz"
}

main $1 $2
