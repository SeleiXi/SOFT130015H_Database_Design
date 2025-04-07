package com.example.databaseimport.service;

import com.example.databaseimport.model.TableDefinition;
import com.example.databaseimport.model.TableDefinition.ColumnDefinition;
import com.example.databaseimport.model.TableDefinition.ForeignKeyDefinition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class CsvImportService {
    
    private static final Logger log = LoggerFactory.getLogger(CsvImportService.class);
    private final DynamicCsvImportService dynamicCsvImportService;

    public CsvImportService(DynamicCsvImportService dynamicCsvImportService) {
        this.dynamicCsvImportService = dynamicCsvImportService;
    }

    @Transactional
    public void initializeDatabase(String roomCsvPath, String studentCsvPath) {
        try {
            // 导入Room表数据
            importRoomData(roomCsvPath);
            
            // 导入Student表数据
            importStudentData(studentCsvPath);
            
        } catch (Exception e) {
            log.error("数据库初始化失败", e);
            throw new RuntimeException("数据库初始化失败", e);
        }
    }

    private void importRoomData(String csvPath) {
        // 定义Room表结构
        TableDefinition roomTable = TableDefinition.builder()
                .tableName("room")
                .columns(List.of(
                        ColumnDefinition.builder()
                                .name("kdno")
                                .type("VARCHAR(10)")
                                .nullable(false)
                                .position(0)
                                .build(),
                        ColumnDefinition.builder()
                                .name("kcno")
                                .type("INT")
                                .nullable(false)
                                .position(1)
                                .build(),
                        ColumnDefinition.builder()
                                .name("ccno")
                                .type("INT")
                                .nullable(false)
                                .position(2)
                                .build(),
                        ColumnDefinition.builder()
                                .name("kdname")
                                .type("VARCHAR(50)")
                                .nullable(true)
                                .position(3)
                                .build(),
                        ColumnDefinition.builder()
                                .name("exptime")
                                .type("DATETIME")
                                .nullable(true)
                                .position(4)
                                .build(),
                        ColumnDefinition.builder()
                                .name("papername")
                                .type("VARCHAR(50)")
                                .nullable(true)
                                .position(5)
                                .build()
                ))
                .primaryKeys(List.of("kdno", "kcno", "ccno"))
                .build();

        // 定义列映射
        Map<Integer, String> columnMappings = new HashMap<>();
        columnMappings.put(0, "kdno");
        columnMappings.put(1, "kcno");
        columnMappings.put(2, "ccno");
        columnMappings.put(3, "kdname");
        columnMappings.put(4, "exptime");
        columnMappings.put(5, "papername");

        // 定义数据转换器
        Map<String, DynamicCsvImportService.ColumnConverter> dataConverters = new HashMap<>();
        dataConverters.put("kcno", DynamicCsvImportService.getIntConverter());
        dataConverters.put("ccno", DynamicCsvImportService.getIntConverter());
        dataConverters.put("exptime", DynamicCsvImportService.getDateConverter());
        dataConverters.put("kdno", DynamicCsvImportService.getStringConverter());
        dataConverters.put("kdname", DynamicCsvImportService.getStringConverter());
        dataConverters.put("papername", DynamicCsvImportService.getStringConverter());

        // 导入数据
        dynamicCsvImportService.importCsvToTable(
                csvPath,
                roomTable,
                false, // room.csv没有表头
                columnMappings,
                dataConverters
        );
    }

    private void importStudentData(String csvPath) {
        // 定义Student表结构
        TableDefinition studentTable = TableDefinition.builder()
                .tableName("student")
                .columns(List.of(
                        ColumnDefinition.builder()
                                .name("registno")
                                .type("VARCHAR(20)")
                                .nullable(false)
                                .position(0)
                                .build(),
                        ColumnDefinition.builder()
                                .name("name")
                                .type("VARCHAR(50)")
                                .nullable(true)
                                .position(1)
                                .build(),
                        ColumnDefinition.builder()
                                .name("kdno")
                                .type("VARCHAR(10)")
                                .nullable(false)
                                .position(2)
                                .build(),
                        ColumnDefinition.builder()
                                .name("kcno")
                                .type("INT")
                                .nullable(false)
                                .position(3)
                                .build(),
                        ColumnDefinition.builder()
                                .name("ccno")
                                .type("INT")
                                .nullable(false)
                                .position(4)
                                .build(),
                        ColumnDefinition.builder()
                                .name("seat")
                                .type("INT")
                                .nullable(true)
                                .position(5)
                                .build()
                ))
                .primaryKeys(List.of("registno"))
                .foreignKeys(List.of(
                        ForeignKeyDefinition.builder()
                                .columns(List.of("kdno", "kcno", "ccno"))
                                .referenceTable("room")
                                .referenceColumns(List.of("kdno", "kcno", "ccno"))
                                .build()
                ))
                .build();

        // 定义列映射
        Map<Integer, String> columnMappings = new HashMap<>();
        columnMappings.put(0, "registno");
        columnMappings.put(1, "name");
        columnMappings.put(2, "kdno");
        columnMappings.put(3, "kcno");
        columnMappings.put(4, "ccno");
        columnMappings.put(5, "seat");

        // 定义数据转换器
        Map<String, DynamicCsvImportService.ColumnConverter> dataConverters = new HashMap<>();
        dataConverters.put("registno", DynamicCsvImportService.getStringConverter());
        dataConverters.put("name", DynamicCsvImportService.getStringConverter());
        dataConverters.put("kdno", DynamicCsvImportService.getStringConverter());
        dataConverters.put("kcno", DynamicCsvImportService.getIntConverter());
        dataConverters.put("ccno", DynamicCsvImportService.getIntConverter());
        dataConverters.put("seat", DynamicCsvImportService.getIntConverter());

        // 导入数据
        dynamicCsvImportService.importCsvToTable(
                csvPath,
                studentTable,
                true, // student.csv有表头
                columnMappings,
                dataConverters
        );
    }
} 