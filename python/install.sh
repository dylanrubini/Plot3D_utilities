#! /bin/bash

echo "y" | pip uninstall plot3d

pip install . --use-feature=in-tree-build --user || pip install . --user