#!/bin/bash
echo "Normal Baseline(10 min)"
./package/tests/mem-burner --malloc 200 --sleep 600 --procs 1

echo "Extended RAM Burst(3 min)"
./package/tests/mem-burner --malloc 3000 --sleep 180 --procs 8 --writef 1.0

echo "Normal Baseline(10 min)"
./package/tests/mem-burner --malloc 400 --sleep 600 --procs 2

echo "High Thread Load(4 min)"
./package/tests/mem-burner --malloc 1000 --sleep 240 --procs 16 --writef 0.8

echo "Normal Baseline(10 min)"
./package/tests/mem-burner --malloc 200 --sleep 600 --procs 1

echo "RAM Spike(1.5 min)"
./package/tests/mem-burner --malloc 4000 --sleep 90 --procs 4 --writef 1.0

echo "Cooldown(5 min)"
./package/tests/mem-burner --malloc 100 --sleep 300 --procs 1

