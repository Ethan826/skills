module CycleNonrecursive.Main where

import Data.Array (concatMap)

data Expr = Var String | Block (Array Expr)

names :: Array Expr -> Array String
names = go
  where
  go = concatMap one
  one (Var s) = [ s ]
  one (Block _) = []
