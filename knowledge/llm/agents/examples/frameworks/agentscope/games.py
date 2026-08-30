from typing import List, Dict, Optional
from agentscope.agent import ReActAgent

"""
【游戏流程】
1.夜晚阶段
狼人讨论：狼人通过 MsgHub 协商击杀目标
预言家查验：预言家选择查验对象
女巫行动：女巫决定是否使用解药/毒药
2.白天阶段
死亡公布：公布夜晚死亡玩家
自由讨论：所有存活玩家参与讨论
投票淘汰：投票选择淘汰对象
猎人技能：被淘汰的猎人可开枪
"""

MAX_GAME_ROUND = 10
MAX_DISCUSSION_ROUND = 3

class WolfGame:

    def __init__(self):
        self.roles: Dict[str, str] = {}
        self.players: Dict[str, ReActAgent] = {}
        self.alive_players: List[ReActAgent] = []
        self.werewolves: List[ReActAgent] = []
        self.villagers: List[ReActAgent] = []
        self.seer: List[ReActAgent] = []      # 预言家
        self.witch: List[ReActAgent] = []     # 女巫
        self.hunter: List[ReActAgent] = []    # 猎人
        
        # 女巫道具状态
        self.witch_has_antidote = True
        self.witch_has_poison = True


    @classmethod
    def get_standard_setup(cls, player_count: int) -> List[str]:
        """获取标准角色配置"""
        if player_count == 6:
            return ["狼人", "狼人", "预言家", "女巫", "村民", "村民"]
        elif player_count == 8:
            return ["狼人", "狼人", "狼人", "预言家", "女巫", "猎人", "村民", "村民"]
        elif player_count == 9:
            return ["狼人", "狼人", "狼人", "预言家", "女巫", "猎人", "守护者", "村民", "村民"]
        else:
            # 默认配置：约1/3狼人
            werewolf_count = max(1, player_count // 3)
            roles = ["狼人"] * werewolf_count
            
            # 添加神职
            remaining = player_count - werewolf_count
            if remaining >= 1:
                roles.append("预言家")
                remaining -= 1
            if remaining >= 1:
                roles.append("女巫")
                remaining -= 1
            if remaining >= 1:
                roles.append("猎人")
                remaining -= 1
            
            # 剩余为村民
            roles.extend(["村民"] * remaining)
            
            return roles