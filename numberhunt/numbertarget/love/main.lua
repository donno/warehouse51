local engine = require('engine')

local game = Game:create()

function love.load()
  love.graphics.setCaption("Number Target")

  font = love.graphics.newFont("LeagueGothic.otf", 54)
  love.graphics.setFont(font)

  local screenWidth = love.graphics.getWidth()
  local screenHeight = love.graphics.getHeight()
  local buttonWidth, buttonHeight = 80, 70
  button = {
    width = buttonWidth,
    padding = 2,
    height = buttonHeight,
    y = screenHeight - buttonHeight - 30,
    startingX = (screenWidth / 2) - (buttonWidth * 3),
    }
  operations = {"+", "-", "/", "*"}
end

function love.draw()
  local screenWidth = love.graphics.getWidth()
  if not game.started then
    love.graphics.setColor(113, 135, 92)
    love.graphics.print('Press ENTER to start!\nPress ESCAPE to quit :(',
                        screenWidth / 2 - 180, 280)
  else
    -- Render the numbers
    local mouseX, mouseY = love.mouse.getPosition()
    for i, v in ipairs(game.numbers) do
      local x = button.startingX + (i-1) * button.width
      local isSelected = mouseX >= x and
        mouseX <= x + button.width and
        mouseY >= button.y and mouseY <= button.y + button.height

      local isDisabled = game.pickedNumbers[i]
      if isDisabled then
        love.graphics.setColor(122, 122, 122)
      elseif isSelected then
        love.graphics.setColor(102, 166, 214)
      else
        love.graphics.setColor(72, 105, 159)
      end

      local p = button.padding
      love.graphics.rectangle("fill",
        x + p, button.y + p, button.width - p - p, button.height - p - p)
      love.graphics.setColor(242, 226, 196)
      love.graphics.print(v, x + p * 2 + 8, button.y + p * 2)
    end

    -- Render the operations
    local y =  button.y - button.height
    for i, v in ipairs(operations) do
      local x = button.startingX + i * button.width
      local isDisabled = #game.playedOperations >= #game.numbers - 1
      local isSelected = mouseX >= x and
        mouseX <= x + button.width and
        mouseY >= y and mouseY <= y + button.height

      if isDisabled then
        love.graphics.setColor(122, 122, 122)
      elseif isSelected then
        love.graphics.setColor(102, 166, 214)
      else
        love.graphics.setColor(72, 105, 159)
      end

      local p = button.padding
      love.graphics.rectangle("fill",
        x + p, y + p, button.width - p - p, button.height - p - p)
      love.graphics.setColor(242, 226, 196)
      love.graphics.print(v, x + p * 2 + 8, y + p * 2)
    end

    -- Render the target in the top left.
    love.graphics.setColor(72, 105, 159)
    love.graphics.rectangle("fill", 20, 20, 120, button.height)
    love.graphics.setColor(242, 226, 196)

    -- TODO: Consider changing this for an LCD-style font.
    love.graphics.print(string.format("[%03d]", game.target), 30, 20)

    -- Draw the current value and time in the top right.
    love.graphics.setColor(72, 105, 159)
    love.graphics.rectangle("fill", screenWidth-230-20, 20, 230, button.height)
    love.graphics.rectangle("fill", screenWidth-80-20, 20+button.height, 80, button.height)
    love.graphics.setColor(242, 226, 196)
    love.graphics.print(string.format("[%9d]", game.current),
                        screenWidth-230, 20)
    love.graphics.print(string.format("%02d", game:timeLeft()), screenWidth-80, 20 + button.height)

    for i, v in ipairs(game.playedNumbers) do
      local y = 20 + (i-1) * button.height
      -- Line up with the 3rd button.
      local x = button.startingX + 2 * button.width  + button.padding
      love.graphics.print(v, x, y)
    end

    for i, v in ipairs(game.playedOperations) do
      -- Line up with the 4th button but 2nd played number.
      local x = button.startingX + 3 * button.width  + button.padding
      local y = 20 + (i * button.height)
      love.graphics.print(v, x, y)
    end

    -- Determine if it is game over and draw it over the top.
    if game:isOver() then
       local y = love.graphics.getHeight() / 2 - button.height * 2
       love.graphics.setColor(72, 105, 159)
       love.graphics.rectangle("fill", button.startingX, y, button.width * 6,
                               button.height * 2)
       love.graphics.setColor(242, 226, 196)
       love.graphics.print("Game over", screenWidth / 2 - 200 / 2, y)

      if (game.target == game.current) then
        love.graphics.print("Spot on", screenWidth / 2 - 200 / 2,
                            y + button.height)
       end
    end
  end
end

function love.update(dt)
  if game.started then
  else
    if love.keyboard.isDown("return") then
      if not game.started then
        game:start()
      end
    end
  end
end

function love.keyreleased(key)
  if key == 'escape' then
    love.event.push("quit")
    return
  end

  if game.started then
    if key == "r" then
      -- Restart
      game.started = False
      game:start()
    elseif key == "kp+" or key == "+" then
      game:performOperation("+")
    elseif key == "kp-" or key == "-" then
      game:performOperation("-")
    elseif key == "kp/" or key == "/" then
      game:performOperation("/")
    elseif key == "kp*" or key == "*" then
      game:performOperation("*")
    else
      -- Use the numbers 1-6 as shortcut keys for the numbers.
      if string.sub(key, 1, 2) == "kp" then
        key = string.sub(key, 3)
      end
      local n = tonumber(key)
      if n and n > 0 and n < 7 then
        game:pick(n)
      end
    end
  end
end

function love.mousepressed(x, y, btn)
  if game.started and btn == 'l' then
    x = x - button.startingX
    if x >= 0 and x <= 6 * button.width then
      -- Determine which one was pressed (operation or number)

      local numberPressed = math.floor(x / button.width)
      if y >= button.y and y <= button.y + button.height then
        -- The first number is 0.
        game:pick(numberPressed+1)

      elseif y >= button.y - button.height and y <= button.y and
             numberPressed > 0 and numberPressed < 5 then
        -- Operations are 1,2,3,4.
        game:performOperation(operations[numberPressed])
      end
    end
  end
end