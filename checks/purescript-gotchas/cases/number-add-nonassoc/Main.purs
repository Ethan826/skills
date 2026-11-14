module NumberAddNonassoc.Main (main) where

import Prelude

import Data.Int (toNumber)
import Effect (Effect)
import Effect.Console (log)
import Random.LCG (Seed, lcgM, lcgNext, mkSeed, unSeed)

triples :: Int
triples = 100000

unitInterval :: Seed -> Number
unitInterval seed = toNumber (unSeed seed) / toNumber lcgM

-- How many of n random triples in [0, magnitude) give
-- (a + b) + c /= a + (b + c). Tail recursive, so it runs in a loop.
differing :: Number -> Int -> Seed -> Int -> Int
differing magnitude n seed acc =
  if n == 0 then acc
  else
    let
      s1 = lcgNext seed
      s2 = lcgNext s1
      s3 = lcgNext s2
      a = magnitude * unitInterval s1
      b = magnitude * unitInterval s2
      c = magnitude * unitInterval s3
      next = if (a + b) + c /= a + (b + c) then acc + 1 else acc
    in
      differing magnitude (n - 1) s3 next

fraction :: Number -> Number
fraction magnitude =
  toNumber (differing magnitude triples (mkSeed 20261114) 0) / toNumber triples

entry :: String -> Number -> String
entry key magnitude = "\"" <> key <> "\": " <> show (fraction magnitude)

main :: Effect Unit
main = log $ "{" <> entry "1" 1.0 <> ", " <> entry "1000" 1.0e3 <> ", "
  <> entry "1000000" 1.0e6 <> ", " <> entry "1000000000" 1.0e9 <> "}"
