"""
Echo Mock System - Agent 状态机与生命周期管理
==============================================
负责根据对话轮次和进度，将面试划分为破冰、简历深挖、技术基础、场景设计、反问等阶段，
并动态加载对应的 System Prompt。
"""

import logging
from typing import Tuple

from app.ai_engine.rag.prompts import (
    STAGE_PROMPTS, INTERVIEWER_SYSTEM_PROMPT, RESUME_CONTEXT_BLOCK,
    ICEBREAK_WITH_RESUME_AND_ROLE, ICEBREAK_WITH_RESUME_ONLY, ICEBREAK_WITH_ROLE_ONLY,
)

logger = logging.getLogger(__name__)


class InterviewStage:
    ICEBREAK = "icebreak"
    RESUME_DIVE = "resume_dive"
    FUNDAMENTALS = "fundamentals"
    SCENARIO = "scenario"
    REVERSE_QA = "reverse_qa"


class InterviewStateMachine:
    """被动状态机（无状态计算器），根据当前轮次计算状态"""

    def __init__(self, target_role: str):
        self.target_role = target_role

    def get_current_stage(self, current_round: int) -> str:
        """
        根据 AI 和 USER 对话的轮次（round_seq 的最大值）判断当前阶段。
        规则 (可灵活调整)：
        - 0-1 轮：破冰与自我介绍
        - 2-4 轮：简历深挖
        - 5-9 轮：技术基础连环问
        - 10-12 轮：场景设计题
        - >=13 轮：反问环节
        """
        if current_round <= 1:
            return InterviewStage.ICEBREAK
        elif current_round <= 4:
            return InterviewStage.RESUME_DIVE
        elif current_round <= 9:
            return InterviewStage.FUNDAMENTALS
        elif current_round <= 12:
            return InterviewStage.SCENARIO
        else:
            return InterviewStage.REVERSE_QA

    def get_stage_prompt(self, current_round: int, resume_text: str = "") -> Tuple[str, str]:
        """
        获取当前阶段的标识和构建好的 Prompt。
        注意: 如阶段包含 {retrieved_questions} 占位符，由调用方负责替换 RAG 知识。
        
        Args:
            current_round: 当前对话轮次
            resume_text: 候选人简历文本（可选）
        
        返回: (stage_name, full_system_prompt_string)
        """
        stage = self.get_current_stage(current_round)
        stage_template = STAGE_PROMPTS.get(stage, STAGE_PROMPTS[InterviewStage.ICEBREAK])

        # 破冰阶段：根据「有无简历 × 有无岗位方向」选择合适的开场指令
        if stage == InterviewStage.ICEBREAK:
            has_resume = bool(resume_text and resume_text.strip())
            has_role = bool(self.target_role and self.target_role.strip())

            if has_resume and has_role:
                icebreak_instruction = ICEBREAK_WITH_RESUME_AND_ROLE.format(
                    target_role=self.target_role
                )
            elif has_resume and not has_role:
                icebreak_instruction = ICEBREAK_WITH_RESUME_ONLY
            elif has_role and not has_resume:
                icebreak_instruction = ICEBREAK_WITH_ROLE_ONLY.format(
                    target_role=self.target_role
                )
            else:
                # 兜底：无简历无岗位，退回初始自我介绍提示
                icebreak_instruction = (
                    "- 请先通过一句轻松的寒暄破冰，然后请候选人介绍一个自己最有代表性的项目或技术经验。"
                )

            stage_template = stage_template.format(icebreak_instruction=icebreak_instruction)

        # 构建简历上下文
        resume_context = ""
        if resume_text:
            resume_context = RESUME_CONTEXT_BLOCK.format(resume_text=resume_text)

        # 包装核心人设（强制注入目标岗位约束 + 简历上下文）
        full_system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
            target_role=self.target_role,
            current_stage=stage_template,
            resume_context=resume_context,
        )

        logger.debug(f"[StateMachine] 计算得出当前阶段: {stage} (Round {current_round}), 简历: {'有' if resume_text else '无'}")
        return stage, full_system_prompt
