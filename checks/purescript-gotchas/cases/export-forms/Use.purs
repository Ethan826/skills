module ExportForms.Use where

import ExportForms.T (T, U(..), V(A, B, C), mkT)

t :: T
t = mkT

us :: Array U
us = [ U1, U2 ]

vs :: Array V
vs = [ A, B, C ]
