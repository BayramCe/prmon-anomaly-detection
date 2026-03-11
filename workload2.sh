#!/bin/bash
echo "Normal Baseline(5 min)"
./package/tests/mem-burner --malloc 150 --sleep 300 --procs 1

echo "Gradual RAM increase anomaly(4 min)"
./package/tests/mem-burner --malloc 200 --sleep 60 --procs 1
./package/tests/mem-burner --malloc 400 --sleep 60 --procs 1
./package/tests/mem-burner --malloc 600 --sleep 60 --procs 1
./package/tests/mem-burner --malloc 800 --sleep 60 --procs 1

echo "Normal Baseline(5 min)"
./package/tests/mem-burner --malloc 150 --sleep 300 --procs 1

echo "IO anomaly burst(3 min)"
./package/tests/io-burner --io 300 --threads 4 --procs 2 --pause 1

echo "Normal Baseline(5 min)"
./package/tests/mem-burner --malloc 150 --sleep 300 --procs 1

echo "Short spike anomalies(6 min)"
./package/tests/mem-burner --malloc 150 --sleep 60 --procs 1
./package/tests/mem-burner --malloc 2000 --sleep 15 --procs 6
./package/tests/mem-burner --malloc 150 --sleep 60 --procs 1
./package/tests/mem-burner --malloc 2500 --sleep 15 --procs 8
./package/tests/mem-burner --malloc 150 --sleep 60 --procs 1
./package/tests/mem-burner --malloc 1800 --sleep 15 --procs 5
./package/tests/mem-burner --malloc 150 --sleep 60 --procs 1

echo "Normal Baseline(4 min)"
./package/tests/mem-burner --malloc 150 --sleep 240 --procs 1

