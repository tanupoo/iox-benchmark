FROM devhub-docker.cisco.com/iox-docker/ir1101/base-rootfs
RUN opkg update
RUN opkg install openssl
RUN (opkg install tzdata ; exit 0)
RUN cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime
COPY build/ /
CMD "/bin/test.sh"
