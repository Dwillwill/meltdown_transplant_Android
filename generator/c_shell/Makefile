CC = /home/nuc/cyk/gcc-arm-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc
target = c_shell_bin
$(target):test.c
	$(CC) $< -static -o $(target)

clean:
	rm $(target)