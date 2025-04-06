package com.example.databaseimport.entity;

import lombok.Data;
import java.util.Date;

@Data
public class Room {
    private String kdno;    // 考点号
    private Integer kcno;   // 考场号
    private Integer ccno;   // 场次号
    private String kdname;  // 考点名称
    private Date exptime;   // 预计开考时间
    private String papername; // 指定试卷号
} 