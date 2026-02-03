"use client";

import { ScriptBlock } from "@/lib/blocks/types";
import ScriptBlockCard from "@/components/ScriptBlockCard";
import { Plus, ArrowUp, ArrowDown } from "lucide-react";
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from "@hello-pangea/dnd";
import { useState } from "react";

interface BlockListPanelProps {
  blocks: ScriptBlock[];
  selectedBlockId: string | null;
  onAddBlock: () => void;
  onSelectBlock: (blockId: string) => void;
  onUpdateBlock: (block: ScriptBlock) => void;
  onDeleteBlock: (blockId: string) => void;
  onDuplicateBlock: (blockId: string) => void;
  onSplitBlock: (blockId: string) => void;
  onAutoSplitBlock: (blockId: string) => void;
  onMergeBlock: (blockId: string) => void;
  onMoveBlockUp: (blockId: string) => void;
  onMoveBlockDown: (blockId: string) => void;
  onReorderBlocks: (reorderedBlocks: ScriptBlock[]) => void;
}

export default function BlockListPanel({
  blocks,
  selectedBlockId,
  onAddBlock,
  onSelectBlock,
  onUpdateBlock,
  onDeleteBlock,
  onDuplicateBlock,
  onSplitBlock,
  onAutoSplitBlock,
  onMergeBlock,
  onMoveBlockUp,
  onMoveBlockDown,
  onReorderBlocks,
}: BlockListPanelProps) {
  const [isDragging, setIsDragging] = useState(false);

  const totalDuration = blocks.reduce((sum, b) => sum + b.duration, 0);
  const minutes = Math.floor(totalDuration / 60);
  const seconds = totalDuration % 60;

  const handleDragEnd = (result: DropResult) => {
    setIsDragging(false);

    const { source, destination, draggableId } = result;

    // 드롭 위치가 없으면 취소
    if (!destination) return;

    // 같은 위치에 드롭하면 무시
    if (
      source.index === destination.index &&
      source.droppableId === destination.droppableId
    ) {
      return;
    }

    // 블록 순서 변경
    const newBlocks = Array.from(blocks);
    const draggedBlock = newBlocks[source.index];
    newBlocks.splice(source.index, 1);
    newBlocks.splice(destination.index, 0, draggedBlock);

    // 순서 업데이트
    onReorderBlocks(newBlocks);
  };

  return (
    <aside className="w-96 bg-[#2a2a2a] border-l border-gray-800 flex flex-col h-screen">
      {/* 헤더: 고정 */}
      <div className="p-4 flex-shrink-0 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-300">
            스크립트 블록 ({blocks.length}개)
          </h2>
          <button
            onClick={onAddBlock}
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded-lg text-xs flex items-center gap-1 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            블록 추가
          </button>
        </div>
        <p className="text-xs text-gray-500">
          총 {minutes}분 {seconds}초
        </p>
      </div>

      {/* 스크롤 영역: 고정 높이 내에서 스크롤 */}
      {blocks.length > 0 ? (
        <DragDropContext
          onDragStart={() => setIsDragging(true)}
          onDragEnd={handleDragEnd}
        >
          <Droppable droppableId="script-blocks">
            {(provided, snapshot) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className={`flex-1 overflow-y-auto px-4 py-4 space-y-3 transition-colors ${
                  snapshot.isDraggingOver ? "bg-[#1a1a1a]" : ""
                }`}
                style={{ maxHeight: "calc(100vh - 120px)" }}
              >
                {blocks.map((block, index) => (
                  <Draggable
                    key={block.id}
                    draggableId={block.id}
                    index={index}
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        className={`relative transition-all duration-200 ${
                          snapshot.isDragging
                            ? "opacity-50 scale-95 shadow-lg"
                            : ""
                        }`}
                      >
                        <ScriptBlockCard
                          block={block}
                          isSelected={selectedBlockId === block.id}
                          onSelect={() => onSelectBlock(block.id)}
                          onUpdate={onUpdateBlock}
                          onDelete={() => onDeleteBlock(block.id)}
                          onDuplicate={() => onDuplicateBlock(block.id)}
                          onSplit={() => onSplitBlock(block.id)}
                          onAutoSplit={() => onAutoSplitBlock(block.id)}
                          onMerge={() => onMergeBlock(block.id)}
                        />

                        {/* 순서 변경 버튼 (선택 시에만 표시) */}
                        {selectedBlockId === block.id && !isDragging && (
                          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex flex-col gap-1 z-10">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onMoveBlockUp(block.id);
                              }}
                              disabled={index === 0}
                              className="p-1.5 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed rounded transition-colors"
                              title="위로 (또는 드래그)"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onMoveBlockDown(block.id);
                              }}
                              disabled={index === blocks.length - 1}
                              className="p-1.5 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed rounded transition-colors"
                              title="아래로 (또는 드래그)"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      ) : (
        <div className="text-center py-8 text-gray-500 text-sm">
          &quot;블록 추가&quot; 버튼으로 스크립트 블록을 생성하세요
        </div>
      )}
    </aside>
  );
}
