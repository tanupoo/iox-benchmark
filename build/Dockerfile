# dev
FROM devhub-docker.cisco.com/iox-docker/ir1101/base-rootfs as builder
RUN opkg update
RUN opkg install coreutils
RUN opkg install git pkgconfig
RUN opkg install iox-toolchain
WORKDIR /build
RUN git clone https://github.com/akopytov/sysbench && \
	cd sysbench && \
	git checkout 1.0.20 && \
	./autogen.sh && \
	./configure --prefix=/build --without-mysql --enable-static && \
	make && \
	make install
RUN mkdir /build/lib && cp /lib/libgcc_s.so* /build/lib/
RUN wget -O linpack.c http://www.netlib.org/benchmark/linpackc.new
RUN gcc -O3 linpack.c -o linpack -lm && \
	mv linpack /build/bin/

# app
FROM devhub-docker.cisco.com/iox-docker/ir1101/base-rootfs
RUN opkg update
RUN opkg install coreutils
RUN opkg install openssl
RUN (opkg install tzdata ; exit 0) && \
	cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime
COPY --from=builder /build/bin/sysbench /bin/
COPY --from=builder /build/bin/linpack /bin/
COPY --from=builder /build/share/sysbench /usr/share/sysbench
COPY --from=builder /build/lib /lib
COPY benchmark.sh /bin/

