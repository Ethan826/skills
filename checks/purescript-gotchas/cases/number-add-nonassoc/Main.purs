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

-- A value uniform on [0, magnitude), or on [-magnitude, magnitude) when
-- signed.
draw :: Boolean -> Number -> Seed -> Number
draw signed magnitude seed =
  if signed then magnitude * (2.0 * unitInterval seed - 1.0)
  else magnitude * unitInterval seed

-- How many of n random triples give (a + b) + c /= a + (b + c).
-- Tail recursive, so it runs in a loop.
differing :: Boolean -> Number -> Int -> Seed -> Int -> Int
differing signed magnitude n seed acc =
  if n == 0 then acc
  else
    let
      s1 = lcgNext seed
      s2 = lcgNext s1
      s3 = lcgNext s2
      a = draw signed magnitude s1
      b = draw signed magnitude s2
      c = draw signed magnitude s3
      next = if (a + b) + c /= a + (b + c) then acc + 1 else acc
    in
      differing signed magnitude (n - 1) s3 next

fraction :: Boolean -> Number -> Number
fraction signed magnitude =
  toNumber (differing signed magnitude triples (mkSeed 20261114) 0)
    / toNumber triples

entry :: Boolean -> String -> Number -> String
entry signed key magnitude =
  "\"" <> (if signed then "signed/" else "positive/") <> key <> "\": "
    <> show (fraction signed magnitude)

entries :: Boolean -> String
entries signed = entry signed "1" 1.0 <> ", " <> entry signed "1000" 1.0e3
  <> ", " <> entry signed "1000000" 1.0e6 <> ", "
  <> entry signed "1000000000" 1.0e9

main :: Effect Unit
main = log $ "{" <> entries false <> ", " <> entries true <> "}"
