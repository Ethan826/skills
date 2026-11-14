module CycleFixed.Main where

import Data.Array (concatMap)

data Expr = Var String | Block (Array Expr)

names :: Array Expr -> Array String
names = go
  where
  go es = concatMap one es
  one (Var s) = [ s ]
  one (Block es) = go es
