#include <iostream>
#include <deque>

int test() {
    std::deque<int> myDeque = {1, 2, 3, 4, 5};

    // 使用逆向迭代器初始化
    std::deque<int>::const_reverse_iterator rit_cur = myDeque.rbegin();

    // 从最后一个元素向前遍历并输出所有元素
    while (rit_cur != myDeque.rend()) {
        std::cout << *rit_cur << " ";
        rit_cur++;
    }

    return 0;
}






