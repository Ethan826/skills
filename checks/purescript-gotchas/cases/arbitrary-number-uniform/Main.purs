module ArbitraryNumberUniform.Main (main) where

import Prelude

import Data.Array (filter, length)
import Data.Foldable (maximum, minimum)
import Data.Maybe (fromMaybe)
import Effect (Effect)
import Effect.Console (log)
import Random.LCG (mkSeed)
import Test.QuickCheck.Arbitrary (arbitrary)
import Test.QuickCheck.Gen (sample)

values :: Array Number
values = sample (mkSeed 20261114) 10000 arbitrary

outside :: Int
outside = length (filter (\x -> x < 0.0 || x >= 1.0) values)

main :: Effect Unit
main = log $ "{\"count\": " <> show (length values)
  <> ", \"min\": " <> show (fromMaybe (-1.0) (minimum values))
  <> ", \"max\": " <> show (fromMaybe 2.0 (maximum values))
  <> ", \"outside\": " <> show outside <> "}"
