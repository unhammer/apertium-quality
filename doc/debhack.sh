#!/bin/bash

# ./setup.py install --prefix ./dest
# 
# * in usr/lib, rename python3.x to python3
# * in python3, rename site-packages to dist-packages
# * delete *.pyc 
# * md5sum everything recursively
# * using template 'control' file, sed in requirements
#
# $ tar zcf control.tar.gz md5sums postinst prerm control
# $ tar zcf data.tar.gz ./usr
# $ echo 2.0 > debian-binary
# $ ar q ${name}.deb debian-binary control.tar.gz data.tar.gz

PYTHON="python3.1"
SETUP="./setup.py"
PKG="./pkg"
DEST="./dest"

author=""
email=""

name=""
version=""
release=""

arch=""
installed_size="" #STUB
deps=""
homepage=""

run_setup() {
	$PYTHON $SETUP install --prefix $DEST
}

rename_to_python3() {
	pushd ${DEST}/usr/lib && mv python3* python3 && popd || 
		echo "Couldn't rename to python3" && exit 1;
}

delete_all_pyc() {
	find ${DEST} -name "*.pyc" | xargs rm || echo "Failed to delete" && exit 1;
}

get_md5sums() {
	pushd $PKG && find * -type f -print0 | xargs -0 md5sum > ${PKG}/md5sums && 
		popd || echo "Failed to md5sum" && exit 1;
}

create_control_file() {
	echo "Package: python3-${name}" > ${PKG}/control
	echo "Source: ${name}" >> ${PKG}/control
	echo "Version: ${version}-${release}" >> ${PKG}/control
	echo "Architecture: ${arch}" >> ${PKG}/control
	echo "Maintainer: ${author} <${email}>" >> ${PKG}/control
	echo "Installed-Size: ${installed_size}" >> ${PKG}/control
	echo "Depends: ${deps}" >> ${PKG}/control
	echo "Section: python" >> ${PKG}/control
	echo "Priority: optional" >> ${PKG}/control
	echo "Homepage: ${homepage}" >> ${PKG}/control
	echo "Description: ${description}" >> ${PKG}/control
	echo " ${description}" >> ${PKG}/control
}

create_prerm() {
	echo '#!/bin/sh' > ${PKG}/prerm
	echo 'set -e' >> ${PKG}/prerm
	echo 'if which py3clean >/dev/null 2>&1; then' >> ${PKG}/prerm
	echo '	py3clean -p python3-${name}' >> ${PKG}/prerm
	echo 'fi' >> ${PKG}/prerm
	chmod a+x ${PKG}/prerm
}

create_postinst() {
	echo '#!/bin/sh' > ${PKG}/postinst
	echo 'set -e' >> ${PKG}/postinst
	echo 'if which py3compile >/dev/null 2>&1; then' >> ${PKG}/postinst
	echo '	py3compile -p python3-${name}' >> ${PKG}/postinst
	echo 'fi' >> ${PKG}/postinst
	chmod a+x ${PKG}/postinst 
}

create_debian_binary() {
	echo '2.0' > ${PKG}/debian-binary
}

create_data_tarball() {
	pushd ${DEST} && tar zcf ${PKG}/data.tar.gz ./usr && popd || 
		"Failed to generate data.tar.gz" && exit 1;
}

create_control_tarball() {
	pushd ${PKG} && tar zcf control.tar.gz control md5sums prerm postinst && 
		popd || echo "Failed to generate control.tar.gz" || exit 1;
}

generate_deb() {
	ar q python3-${name}_${version}-${release}_${arch}.deb ||
		echo "Failed to generate deb." && exit 1;
}


main() {
	run_setup
	rename_to_python3
	delete_all_pyc
	get_md5sums
	create_control_file
	create_prerm
	create_postinst
	create_debian_binary
	create_data_tarball
	create_control_tarball
	generate_deb
}
