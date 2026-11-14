module JsBigintsNative.Main (main) where

import Prelude

import JS.BigInt as BigInt
import Effect (Effect)
import Effect.Console (log)

main :: Effect Unit
main = log (BigInt.toString (BigInt.fromInt 42))
