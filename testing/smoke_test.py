"""构建冒烟测试：验证 veloxframe 可正常导入与基础运算。

用于 CI 构建后验证（build-and-test job 安装 wheel 后执行），
以及本地 `./build_wheel.sh` 构建后的快速自检。
"""

import veloxframe as rpd


def main() -> None:
    print(f"veloxframe version: {rpd.__version__}")
    s = rpd.Series([1, 2, 3, 4, 5])
    print(f"Series: {list(s.values)}")
    print(f"Sum: {s.sum()}")
    df = rpd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    print(f"DataFrame shape: ({df.shape[0]}, {df.shape[1]})")
    print("All smoke tests passed!")


if __name__ == "__main__":
    main()
