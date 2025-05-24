import json
import os
from typing import Dict, List, Union, Any


# --- 日志记录函数 ---
def log(*args: Any, **kwargs: Any) -> None:
    """
    简单的日志记录功能，将参数打印到标准输出。
    """
    print("[LOG]", *args, **kwargs) # 添加一个简单的前缀以区分普通print

# --- JSON 文件读取函数 ---
def read_json(conf_file: str) -> Union[Dict[str, Any], List[Any]]:
    """
    从指定路径读取并解析JSON文件。
    """
    log(f"尝试读取JSON文件: '{conf_file}'")
    try:
        with open(conf_file, 'r', encoding='UTF-8') as file:
            data = json.load(file)
            log(f"成功读取并解析JSON文件: '{conf_file}'")
            return data
    except FileNotFoundError as e:
        log(f"错误: JSON文件未找到 - '{conf_file}' - {e}")
        raise
    except json.JSONDecodeError as e:
        log(f"错误: 解析JSON文件失败 - '{conf_file}' - {e}")
        raise
    except OSError as e:
        log(f"错误: 读取JSON文件时发生OS错误 - '{conf_file}' - {e}")
        raise
    except Exception as e:
        log(f"错误: 读取JSON文件时发生未知错误 - '{conf_file}' - {e}")
        raise

# --- 宠物动作重命名函数 ---
def rename_pet_action(pet_name: str, start_idx: int) -> None:
    """
    根据宠物名重命名指定动作文件夹下的所有文件（假定为图片），按顺序列出并从 start_idx 开始编号。
    注意: 重命名基于 os.listdir() 返回的顺序，该顺序不保证跨平台或多次运行一致。
    """
    # 使用 os.path.join 构建路径
    base_path = os.path.join('..', 'res', 'role', pet_name, 'action')
    log(f"开始重命名操作: 目录='{base_path}', 起始索引={start_idx}")

    try:
        filenames = os.listdir(base_path)
        log(f"找到 {len(filenames)} 个条目在目录 '{base_path}' 中.")

        processed_count = 0
        skipped_count = 0
        # 迭代处理找到的每个条目
        for i, current_filename in enumerate(filenames):
            current_filepath = os.path.join(base_path, current_filename)

            if not os.path.isfile(current_filepath):
                log(f"跳过: '{current_filename}' 不是一个文件.")
                skipped_count += 1
                continue # 跳过非文件项

            # 构建新的文件名和完整路径 (保持原逻辑，后缀固定为.png)
            new_filename = f"{start_idx + i}.png"
            new_filepath = os.path.join(base_path, new_filename)

            # 避免不必要的自我重命名
            if current_filepath == new_filepath:
                log(f"跳过: 文件 '{current_filename}' 已是目标名称 '{new_filename}'.")
                skipped_count += 1
                continue

            # 执行重命名操作
            try:
                log(f"尝试重命名: '{current_filename}' -> '{new_filename}'")
                os.rename(current_filepath, new_filepath)
                log(f"成功重命名: '{current_filename}' -> '{new_filename}'")
                processed_count += 1
            except OSError as e:
                # 记录重命名时可能发生的错误 (例如权限问题, 文件正在使用, 目标文件已存在且无法覆盖等)
                log(f"错误: 重命名文件 '{current_filename}' 到 '{new_filename}' 失败 - {e}")
                # 重新抛出异常，以保持与原始代码相同的失败行为（遇到错误即停止）
                raise
            except Exception as e:
                log(f"错误: 重命名文件 '{current_filename}' 时发生未知错误 - {e}")
                raise # 重新抛出未知异常

        log(f"重命名操作完成: 处理了 {processed_count} 个文件, 跳过了 {skipped_count} 个条目.")

    except FileNotFoundError:
        # 由 os.listdir() 抛出
        log(f"错误: 目录不存在 '{base_path}'.")
        raise # 重新抛出，保持接口行为
    except OSError as e:
        # 可能在 os.listdir() 时发生 (如权限不足)
        log(f"错误: 处理目录 '{base_path}' 时发生OS错误 - {e}")
        raise # 重新抛出
    except Exception as e:
        log(f"错误: 重命名过程中发生未知错误 - {e}")
        raise # 重新抛出

# --- 宠物动作删除函数 ---
def remove_pet_action(pet_name: str) -> None:
    """
    删除指定宠物动作文件夹下的所有文件。
    """
    # 使用 os.path.join 构建路径
    base_path = os.path.join('..', 'res', 'role', pet_name, 'action')
    log(f"开始删除操作: 目录='{base_path}'")

    # 同样，让 os.listdir 自然处理 FileNotFoundError
    try:
        filenames = os.listdir(base_path)
        log(f"找到 {len(filenames)} 个条目在目录 '{base_path}' 中.")

        deleted_count = 0
        skipped_count = 0
        # 迭代处理找到的每个条目
        for filename in filenames:
            filepath = os.path.join(base_path, filename)

            # 关键：只尝试删除文件，os.remove 不能删除目录
            if os.path.isfile(filepath):
                try:
                    log(f"尝试删除文件: '{filename}'")
                    os.remove(filepath)
                    log(f"成功删除文件: '{filename}'")
                    deleted_count += 1
                except OSError as e:
                    log(f"错误: 删除文件 '{filename}' 失败 - {e}")
                    raise # 重新抛出，保持原始失败行为
                except Exception as e:
                    log(f"错误: 删除文件 '{filename}' 时发生未知错误 - {e}")
                    raise # 重新抛出
            # 对非文件（如子目录）进行日志记录并跳过
            elif os.path.isdir(filepath):
                 log(f"跳过: '{filename}' 是一个目录.")
                 skipped_count += 1
            else:
                 log(f"跳过: '{filename}' 不是一个文件或目录.")
                 skipped_count += 1

        log(f"删除操作完成: 删除了 {deleted_count} 个文件, 跳过了 {skipped_count} 个条目.")

    except FileNotFoundError:
        log(f"错误: 目录不存在 '{base_path}'.")
        raise # 重新抛出
    except OSError as e:
        log(f"错误: 处理目录 '{base_path}' 时发生OS错误 - {e}")
        raise # 重新抛出
    except Exception as e:
        log(f"错误: 删除过程中发生未知错误 - {e}")
        raise # 重新抛出


# --- 主程序入口 ---
if __name__ == '__main__':
    """
    这个代码块仅在脚本作为主程序直接运行时执行。
    """
    log("脚本开始执行...")
    
    log("--- 开始执行 rename_pet_action 示例 ---")
    try:
        # 假设 'test' 宠物及其动作目录存在
        target_pet = 'test'
        start_index = 29
        rename_pet_action(target_pet, start_index)
        log(f"示例 rename_pet_action('{target_pet}', {start_index}) 执行成功。")
    except Exception as e:
        log(f"示例 rename_pet_action 执行失败: {type(e).__name__} - {e}")
    log("--- rename_pet_action 示例结束 ---")

    log("脚本执行完毕.")
