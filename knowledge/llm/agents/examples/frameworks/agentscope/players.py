from agentscope.agent import ReActAgent, AgentBase
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIMultiAgentFormatter 
from dotenv import load_dotenv
import random
import os
from typing import Dict, List
from prompts import ChinesePrompts
from roles import GameRole
from logs import create_agent_logger

load_dotenv()

MODELSCOPE_MODEL = OpenAIChatModel(
    model_name=os.getenv("MODEL_ID"),  
    client_kwargs={
        "base_url": os.getenv("BASE_URL"),
        # "api_key": os.getenv("API_KEY"), 
        },
    generate_kwargs={"temperature": 0.3, "max_tokens": 1000},
)

def format_player_list_str(players: List[str]) -> str:
    """格式化玩家姓名列表"""
    if not players:
        return "无人"
    return "、".join(players)

class GameModerator(AgentBase):
    """中文版游戏主持人"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "游戏主持人"
        self.game_log: List[str] = []
    
    async def announce(self, content: str) -> Msg:
        """发布游戏公告"""
        msg = Msg(
            name=self.name,
            content=f"📢 {content}",
            role="system"
        )
        self.game_log.append(content)
        await self.print(msg)
        print(msg.content)
        return msg
    
    async def night_announcement(self, round_num: int) -> Msg:
        """夜晚阶段公告"""
        content = f"🌙 第{round_num}夜降临，天黑请闭眼..."
        return await self.announce(content)
    
    async def day_announcement(self, round_num: int) -> Msg:
        """白天阶段公告"""
        content = f"☀️ 第{round_num}天天亮了，请大家睁眼..."
        return await self.announce(content)
    
    async def death_announcement(self, dead_players: List[str]) -> Msg:
        """死亡公告"""
        if not dead_players:
            content = "昨夜平安无事，无人死亡。"
        else:
            content = f"昨夜，{format_player_list_str(dead_players)}不幸遇害。"
        return await self.announce(content)

    async def vote_result_announcement(self, voted_out: str, vote_count: int) -> Msg:
        """投票结果公告"""
        content = f"投票结果：{voted_out}以{vote_count}票被淘汰出局。"
        return await self.announce(content)
    
    async def game_over_announcement(self, winner: str) -> Msg:
        """游戏结束公告"""
        content = f"🎉 游戏结束！{winner}"
        return await self.announce(content)
    


class GamePlayer:
    CHARACTER_TRAITS = {
        "刘备": "仁德宽厚，善于团结众人，说话温和有礼",
        "关羽": "忠义刚烈，言辞直接，重情重义",
        "张飞": "性格豪爽，说话大声直接，容易冲动",
        "诸葛亮": "智慧超群，分析透彻，言辞谨慎",
        "赵云": "忠勇双全，话语简洁有力",
        "曹操": "雄才大略，善于权谋，话语犀利",
        "司马懿": "深谋远虑，城府极深，言辞含蓄",
        "周瑜": "才华横溢，略显傲气，分析精准",
        "孙权": "年轻有为，善于决断，话语果决"
    }

    CHINESE_NAMES = [
            "刘备", "关羽", "张飞", "诸葛亮", "赵云",
            "曹操", "司马懿", "典韦", "许褚", "夏侯惇", 
            "孙权", "周瑜"
        ]

    @classmethod
    def get_chinese_name(cls, character: str = None) -> str:
        """获取中文角色名"""
        if character and character in cls.CHINESE_NAMES:
            return character
        return random.choice(cls.CHINESE_NAMES)

    @classmethod
    def get_character_trait(cls, character: str) -> str:
        """获取角色性格特点"""
        return cls.CHARACTER_TRAITS.get(character, "性格温和，说话得体")
    
    @staticmethod
    async def create_player(character: str, role: str, moderator: GameModerator) -> ReActAgent:
        """
        创建具有三国背景的玩家
        - character: 游戏名
        - role：角色
        - moderator：DM
        """
        name = GamePlayer.get_chinese_name(character)
        sys_prompt = ChinesePrompts.get_role_prompt(role, character, GamePlayer.get_character_trait(character))
        
        agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=MODELSCOPE_MODEL,
            formatter=OpenAIMultiAgentFormatter(),
        )

        agent.logger = create_agent_logger(name)
        agent.logger.debug(f"[系统提示词]{sys_prompt}")

        # 角色身份确认
        await agent.observe(
            await moderator.announce(
                f"【{name}】你在这场三国狼人杀中扮演{GameRole.get_role_desc(role)}，"
                f"你的技能：{GameRole.get_role_ability(role)}"
            )
        )
        
        return agent