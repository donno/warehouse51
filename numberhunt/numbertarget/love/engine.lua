--
-- Game
--   Variables
--     * numbers - The array of six numbers that the player can use in the game.
--     * target - The number the player has to reach.
--     * started - True if the game is started.
--
--     * current - The latest number computed.
--     * playedNumbers - The list of numbers used.
--     * playedOperations - The list of operations used.
--
--   Methods
--     * create - Creates the game
--     * start - Starts the game (generates the numbers and target).
--     * pick - Picks one of the numbers. (supceeds useNumber)
--     * useNumber - Plays the given number.
--     * performOperation - Performs the given operation.

Game = {}
function Game:create()
  math.randomseed(os.time())
  o = o or {}
  setmetatable(o, self)
  self.__index = self
  o.started = false
  return o
end

function Game:start()
  -- Generate the numbers.
  if self.started then
    assert(self.started, "The game is already started")
    return
  end

  -- The pool of numbers are the four larges below and two of each number from
  -- 1 to 10.
  local numbers = {25, 50, 75, 100}
  for small = 1, 10 do
    numbers[4 + small]  = small
    numbers[4 + small + 10]  = small
  end

  -- Shuffle the numbers and the first six numbers become the numbers the player
  -- can use in the game.
  -- shuffle(numbers)

  self.numbers = {}
  for i = 1, 6 do
    self.numbers[i] = numbers[i]
  end

  -- Generate the target ('CECIL')
  -- self.target = math.random(101, 999)
  self.target = 500

  -- Set up the time limit
  self.timeLimit = 10

  -- Set up the rest of the 'in progress' state such as what numbers have been
  -- used and what operations invoked.
  self.playedNumbers = {}
  self.playedOperations = {}
  self.current = 0

  self.pickedNumbers = {
    [1]=false, [2]=false, [3]=false, [4]=false, [5]=false, [6]=false}

  -- Flag the game as started.
  self.started = true

  self.winner = true

  -- Record the start time as the player only has 60 seconds.
  self.startTime = os.time()
  self.currentTime = os.time()
end

function Game:pick(index)
  -- Returns true on a valid move and false otherwise
  --
  -- An move is considered invalid if the index given is out of bounds OR
  -- the number has already been played.
  --
  if index < 1 or index > #self.numbers then
    error("Index out of bounds")
    return false -- Illegal move
  end

  if not self.started or self:isOver() then
    return false -- Game is not in progress.
  end

  if not self.pickedNumbers[index] then
    self.pickedNumbers[index] = true

    -- Now keeps track of the order that the numbers were played. This is to
    -- help the calucation as well as for making it easy to do the UI.
    table.insert(self.playedNumbers, self.numbers[index])
    self:calcuateCurrentNumber()
    return true
  end
  return false
end

function Game:isOver()
   -- Returns true if the game is over, otherwise false.
   --
   -- The game is over if the player has used all the numbers and operations
   -- OR the player has reached the number
   -- OR the player has ran out of time.
   return ((#self.playedNumbers == #self.numbers and
            #self.playedOperations == #self.numbers - 1) or
            self.target == self.current or
            (self.currentTime - self.startTime) >= self.timeLimit)
end

function Game:performOperation(operation)
  if not self.started or self:isOver() then
    return
  end

  -- If there are N numbers then only N-1 operations can be done.
  if #self.playedOperations < #self.numbers - 1 then
    table.insert(self.playedOperations, operation)
    self:calcuateCurrentNumber()
  end
end

function Game:calcuateCurrentNumber(operation)
  -- Take two operands from the playedNumbers and an operation .
  local accumlator = self.playedNumbers[1]

  for i = 2, #self.playedNumbers do
    local operand = self.playedNumbers[i]
    local operation = self.playedOperations[i-1]

    if operation == "/" then
      -- TODO: Enforce this is only interger division.
      accumlator = accumlator / operand
    elseif operation == "+" then
      accumlator = accumlator + operand
    elseif operation == "*" then
      accumlator = accumlator * operand
    elseif operation == "*" then
      error("Unrecognised operation: " .. operation)
    end
  end

  if accumlator then
    self.current = accumlator
  end
end

function Game:timeLeft()
  if self.started then
    if not self:isOver() then
      self.currentTime = os.time()
    end
    return self.timeLimit - (self.currentTime - self.startTime)
  else
    return 30
  end
end

-- Helper function for determining if value is already in a table t.
function find(t, value)
  for i,v in ipairs(t) do
    if v == value then
      return true
    end
  end
  return false
end

-- Helper function to shuffle an table t.
function shuffle(t)
  local n = #t
  while n >= 2 do
    local k = math.random(n) -- 1 <= k <= n
    t[n], t[k] = t[k], t[n]
    n = n - 1
  end
  return t
end

return Game