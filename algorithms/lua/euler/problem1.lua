-----------------------------------
-- Problem 1
-- If we list all the natural numbers below 10 that are multiples of 3 or 5,
-- we get 3, 5, 6 and 9. The sum of these multiples is 23.

-- Find the sum of all the multiples of 3 or 5 below 1000.
--
--
-- Solution by Donno <darkdonno@gmail.com
-----------------------------------

function problem1 (maxSum)
  -- Solves problem 1 of project euler.
  -- Find the sum of all the multiples of 3 or 5 below 1000.
  --
  -- \param maxSum

  assert( maxSum >= 1 )

  local sum = 0
  local maxIter = math.max(maxSum / 3, maxSum / 5)

  for n = 3, maxSum-1, 3 do
    sum = sum + n
  end

  for n = 5, maxSum-1, 5 do
    if (5 * n) % 3 ~= 0 then
      sum = sum + n
    end
  end

  return sum
end

-- Evaluates an problem
io.write(problem1(1000), '\n')
