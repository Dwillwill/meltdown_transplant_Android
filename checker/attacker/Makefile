CC                   = /home/nuc/cyk/gcc-arm-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc
AS                   = /home/nuc/cyk/gcc-arm-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc
LD                   = /home/nuc/cyk/gcc-arm-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc
CFLAGS              += -D_GNU_SOURCE -DNO_TSX=1 -O0 -w
INCLUDE              = -I.
LDFLAGS             += $(SUBDIRS:%=-L %) -lpthread

SOURCES              = $(shell ls *.c)
OBJECTS              = $(SOURCES:.c=.o) autogen.o medusa.o
OUTPUT               = attacker

BUILDDIRS            = $(SUBDIRS:%=build-%)
CLEANDIRS            = $(SUBDIRS:%=clean-%)

.SILENT:
all: $(OUTPUT)

$(OUTPUT): $(BUILDDIRS) $(OBJECTS)
	# echo "$(INDENT)[LD]" $(OBJECTS) $(LIBS) -o $(OUTPUT) 
	$(LD) $(OBJECTS) -no-pie -static $(LDFLAGS) -o $(OUTPUT) 

%.o : %.c
	# echo "$(INDENT)[CC] " $<
	# echo $(CC) $(CFLAGS) $(INCLUDE) -c $<
	$(CC) $(CFLAGS) $(INCLUDE) -c $<

%.o : %.S
	# echo "$(INDENT)[AS] " $<
	# echo $(AS) $(INCLUDE) -c $< -o $@
	$(AS) $(INCLUDE) -c $< -o $@

clean: $(CLEANDIRS)
	# echo "$(INDENT)[RM]" $(OBJECTS) $(OUTPUT)
	rm -f $(OBJECTS) $(OUTPUT)
