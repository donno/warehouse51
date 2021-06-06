---------------------------------
-- Calculates the n-th Fibonacci
-- By Donno <darkdonno@gmail.com
---------------------------------

function fib(n)
  -- Calcuates the n-th Fibonacci number.
  --
  -- \param n the n-th number in the Fibonacci sequence
  -- \return the n-th Fibonacci number
  --
  local last = 0
  local secondlast = 1

  repeat
    last = last + secondlast
    secondlast = last - secondlast
    n = n - 1
  until not (n > 0)

  until
  return last
end

-- Calcuate the first 10 fibonacci numbers
for n=0,10,1 do
  io.write ( n, ' ', fib(n), '\n' )
end
