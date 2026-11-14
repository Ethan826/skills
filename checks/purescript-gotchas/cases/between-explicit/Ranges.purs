module BetweenExplicit.Ranges (between, inRange) where

import Prelude hiding (between)

between :: Int -> Int -> Int -> Boolean
between low high x = low <= x && x <= high

inRange :: Int -> Int -> Int -> Boolean
inRange = between
