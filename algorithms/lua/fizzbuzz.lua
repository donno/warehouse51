
for n=1,100 do
    if (n % 3 == 0 and n % 5 == 0 ) then
        io.write ( "FizzBuzz\n" )
    elseif (n % 3 == 0) then
        io.write ( "Fizz\n" )
    elseif ( n % 5 == 0 ) then
        io.write ( "Buzz\n" )
    else
        io.write ( n )
        io.write ( "\n")
    end
end
