.method static void main(){
    .entrypoint
    .maxstack 1
    ldstr "Hello world!"
    call void [mscorlib]System.Console::WriteLine(string)
    ret
}

//.method privatescope static void  main$PST06000001() cil managed
//{
  //.entrypoint
  /// Code size       11 (0xb)
  //.maxstack  1
  //IL_0000:  ldstr      "Hello world!"
  //IL_0005:  call       void [mscorlib]System.Console::WriteLine(string)
  //IL_000a:  ret
//} // end of method 'Global Functions'::main

