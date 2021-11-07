local engine = require('engine')
local game = Game:create()
game:start()

print(string.format("The target to reach is %03d", game.target))

local numbers = game.numbers[1]
for i = 2, #game.numbers do
  numbers = numbers .. ', ' .. game.numbers[i]
end

print(string.format("\nThe numbers are %s", numbers))

-- Okay go time.
--
-- For a target of 500 with the numbers 25, 50, 75, 100, 1, 2
--
-- We want  75/25 = 3  then add 2 for 5 then mulply by 100.

-- Error TEST (make sure we have the number)
-- game:useNumber(5)

game:pick(3)
game:performOperation("/")
game:pick(1)
game:performOperation("+")
game:pick(6)
game:performOperation("*")
game:pick(4)

print(string.format("\nYou are at %d", game.current))