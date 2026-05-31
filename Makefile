# 
# 1. General Compiler Settings
#
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

CXX       = g++
CXXFLAGS  = -std=c++11 -Wall -Wextra -Wcast-qual -fno-exceptions -fno-rtti \
            -pedantic -Wno-long-long -msse4.2 -D__STDC_CONSTANT_MACROS -fopenmp
INCLUDES  =
LDFLAGS   =
LIBRARIES = -lpthread

# macOS (Apple Clang): C++ headers, OpenMP, and x86_64 on Apple Silicon (SSE 4.2)
ifeq ($(UNAME_S),Darwin)
  SDK_PATH := $(shell xcrun --show-sdk-path)
  INCLUDES += -I$(SDK_PATH)/usr/include/c++/v1
  CXXFLAGS := $(filter-out -fopenmp,$(CXXFLAGS))
  CXXFLAGS += -Xpreprocessor -fopenmp
  ifeq ($(UNAME_M),arm64)
    # 技巧は SSE 4.2 前提のため、Apple Silicon では x86_64 (Rosetta) でビルドする
    CXXFLAGS += -arch x86_64
    LIBOMP_DIR := lib/libomp-x86_64
    INCLUDES += -I$(LIBOMP_DIR)/include
    LDFLAGS  += -L$(LIBOMP_DIR)/lib -Wl,-rpath,@loader_path/../lib/libomp-x86_64/lib
    LIBRARIES += -L$(LIBOMP_DIR)/lib -lomp
  else
    LIBOMP_PREFIX := $(shell brew --prefix libomp 2>/dev/null)
    ifneq ($(LIBOMP_PREFIX),)
      INCLUDES += -I$(LIBOMP_PREFIX)/include
      LDFLAGS  += -L$(LIBOMP_PREFIX)/lib -Wl,-rpath,$(LIBOMP_PREFIX)/lib
      LIBRARIES += -L$(LIBOMP_PREFIX)/lib -lomp
    endif
  endif
endif

#
# 2. Target Specific Settings
#
ifeq ($(TARGET),gikou)        # Windowsの実行ファイル
	sources  := $(shell ls src/*.cc)
	CXXFLAGS += -O3 -DNDEBUG -DMINIMUM -DPSEUDO_RANDOM_DEVICE -static
endif
ifeq ($(TARGET),release)      # Mac / Linuxの実行ファイル
	sources  := $(shell ls src/*.cc)
	CXXFLAGS += -O3 -DNDEBUG
endif
ifeq ($(TARGET),cluster)      # 疎結合並列探索のマスター側（デバッグ用、assertマクロON）
	sources  := $(shell ls src/*.cc)
	CXXFLAGS += -O3 -DCLUSTER
endif
ifeq ($(TARGET),consultation) # 合議アルゴリズムのマスター側（デバッグ用、assertマクロON）
	sources  := $(shell ls src/*.cc)
	CXXFLAGS += -O3 -DCONSULTATION
endif
ifeq ($(TARGET),development)  # 開発用・デバッグ用
	sources  := $(shell ls src/*.cc)
	CXXFLAGS += -O2 -g3
endif
ifeq ($(TARGET),profile)      # プロファイル用
	sources  := $(shell ls src/*.cc)
	CXXFLAGS += -O3 -DNDEBUG -pg
endif
ifeq ($(TARGET),test)         # ユニットテスト用（Google Testを利用）
	sources  := $(shell ls src/*.cc test/*.cc test/common/*.cc)
	sources  += lib/gtest-1.7.0/fused-src/gtest/gtest-all.cc
	CXXFLAGS += -g3 -Og -DUNIT_TEST
	INCLUDES += -Isrc -Ilib/gtest-1.7.0/fused-src
endif
ifeq ($(TARGET),coverage)     # カバレッジテスト用（Google Testを利用）
	sources  := $(shell ls src/*.cc test/*.cc test/common/*.cc)
	sources  += lib/gtest-1.7.0/fused-src/gtest/gtest-all.cc
	CXXFLAGS += -g3 -DUNIT_TEST -ftest-coverage -fprofile-arcs
	INCLUDES += -Isrc -Ilib/gtest-1.7.0/fused-src
endif

#
# 3. Default Settings (applied if there is no target-specific settings)
#
output_file  ?= bin/$(TARGET)
object_dir   ?= obj/$(TARGET)
objects      ?= $(sources:%.cc=$(object_dir)/%.o)
dependencies ?= $(objects:%.o=%.d)
directories  ?= $(sort $(dir $(objects))) bin

#
# 4. Public Targets
#
.PHONY: gikou release cluster consultation development profile test coverage run-coverage clean scaffold libomp-x86_64

gikou release cluster consultation development profile test coverage:
	$(MAKE) TARGET=$@ executable

run-coverage: coverage
	bin/coverage --gtest_output=xml

clean:
	rm -rf obj/*

scaffold:
	mkdir -p src test bin/data doc lib obj resource

# Apple Silicon 向け x86_64 版 OpenMP ランタイム（初回のみ必要）
libomp-x86_64:
ifeq ($(UNAME_S)-$(UNAME_M),Darwin-arm64)
	@command -v cmake >/dev/null || { echo "cmake が必要です: brew install cmake"; exit 1; }
	mkdir -p lib/libomp-x86_64
	cd /tmp && rm -rf gikou-libomp-build && mkdir gikou-libomp-build && cd gikou-libomp-build && \
	curl -fsSL -o llvm.tar.xz "https://github.com/llvm/llvm-project/releases/download/llvmorg-22.1.6/llvm-project-22.1.6.src.tar.xz" && \
	tar xf llvm.tar.xz && cd llvm-project-22.1.6.src && \
	cmake -S runtimes -B build/shared \
	  -DCMAKE_OSX_ARCHITECTURES=x86_64 \
	  -DCMAKE_OSX_SYSROOT="$$(xcrun --show-sdk-path)" \
	  -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
	  -DCMAKE_INSTALL_PREFIX="$(CURDIR)/lib/libomp-x86_64" \
	  -DCMAKE_CXX_FLAGS="-I$$(xcrun --show-sdk-path)/usr/include/c++/v1" \
	  -DLIBOMP_INSTALL_ALIASES=OFF \
	  -DLLVM_ENABLE_RUNTIMES=openmp \
	  -DOPENMP_ENABLE_OMPT_TOOLS=OFF \
	  -DLLVM_INCLUDE_TESTS=OFF \
	  -DCMAKE_BUILD_TYPE=Release && \
	cmake --build build/shared --target omp -j$$(sysctl -n hw.ncpu) && \
	cmake --install build/shared
else
	@echo "libomp-x86_64 は Apple Silicon (arm64) Mac でのみ必要です"
endif

#
# 5. Private Targets
#
.PHONY: executable
executable: $(directories) $(objects)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $(output_file) $(objects) $(LIBRARIES)
	
$(directories):
	mkdir -p $@

$(object_dir)/%.o: %.cc
	$(CXX) -c -MMD -MP -o $@ $(CXXFLAGS) $(INCLUDES) $<

-include $(dependencies)