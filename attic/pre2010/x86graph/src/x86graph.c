#include <stdio.h>
#include "udis86.h"

int main(int argc, const char *argv[]){
    if (argc != 2) {
        printf("usage: %s filename\n", argv[0]);
        return 1;
    }
    
    printf("Building graph for %s\n", argv[1]);
    FILE *inputFile = fopen(argv[1], "rb");
    if (inputFile == NULL) {
        printf("Error: specified file is invalid\n");
        return 0;
    }
    ud_t ud_obj;
    ud_t *ud_objp = &ud_obj;
    
    ud_init(ud_objp);
    ud_set_input_file(ud_objp, inputFile);
    ud_set_mode(ud_objp, 32);
    ud_set_syntax(ud_objp, UD_SYN_ATT /*UD_SYN_INTEL*/);

    ud_set_pc(ud_objp, 0x004013a4);
    uint64_t programcounter = ud_obj.pc;
    
    ud_disassemble(ud_objp);
    printf("\t%s\n", ud_insn_asm(ud_objp));
    ud_disassemble(ud_objp);
    printf("\t%s\n", ud_insn_asm(ud_objp));

    fclose(inputFile);
    return 0;
}
