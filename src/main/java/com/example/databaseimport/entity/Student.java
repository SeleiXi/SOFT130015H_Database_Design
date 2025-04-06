package com.example.databaseimport.entity;

import lombok.Data;

@Data
public class Student {
    // 以下注释是根据给的文档写的
    private String registno;  // 考号
    private String name;      // 姓名
    private String kdno;      // 考点号
    private Integer kcno;     // 考场号
    private Integer ccno;     // 场次号
    private Integer seat;     // 指定座位，0表示不指定座位
} 