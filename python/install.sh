#! /bin/bash

pip uninstall plot3d

pip install . --use-feature=in-tree-build --user || pip install . --user