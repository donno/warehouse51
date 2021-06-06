-----------------------------------
-- Evaluates the Collatz conjecture
-- By Donno <darkdonno@gmail.com
-----------------------------------

function collatz (n)
  -- Performs the Collatz function on n
  -- Prints out the number before each change
  --
  -- \param n the number to start with

  assert( n >= 1 )

  while n > 1 do
    io.write(n, '\n')
    if n % 2 == 0 then -- n is even
      n = n / 2
    else -- n is odd
      n = n * 3 + 1
    end
  end

  io.write( (n % 2), '\n')

end

-- Evaluates an example
collatz(15)
